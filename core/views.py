from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from dotenv import load_dotenv
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from io import BytesIO
from .models import SlackToken
from .slack_exceptions import handle_slack_exception
from .exceptions import custom_exception_handler
import requests

load_dotenv()

class SlackFileUploadView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]
        
    def post(self, request):
        
        try:
            access_token = SlackToken.objects.get(user=request.user).access_token
            channel_id = request.data['channel_id']
            message = request.data['message']
            file = request.data['file']
            file_bytes = file.read()
            file_io = BytesIO(file_bytes)

            try:
                client = WebClient(token=access_token)

            except SlackApiError as e:
                # Handle Slack API-specific errors
                response = handle_slack_exception(e)
                return response

            except Exception as exc:
                # Handle all other types of exceptions
                response = custom_exception_handler(exc, self.get_renderer_context())
                return response

            try:
                response = client.conversations_info(channel=channel_id)
                if response['channel'].get('is_member') is False:
                    try:
                        response = client.conversations_join(channel=channel_id)

                    except SlackApiError as e:
                        # Handle Slack API-specific errors
                        response = handle_slack_exception(e)
                        return response

                    except Exception as exc:
                        # Handle all other types of exceptions
                        response = custom_exception_handler(exc, self.get_renderer_context())
                        return response
                    
                try:
                    client.files_upload_v2(channel=channel_id, file=file_io, initial_comment=message)
                    return Response({"message": "File uploaded successfully"},status=status.HTTP_200_OK)
                
                except SlackApiError as e:
                         # Handle Slack API-specific errors
                         response = handle_slack_exception(e)
                         return response

                except Exception as exc:
                    # Handle all other types of exceptions
                    response = custom_exception_handler(exc, self.get_renderer_context())
                    return response
            
            except SlackApiError as e:
                # Handle Slack API-specific errors
                response = handle_slack_exception(e)
                return response
            
            except Exception as e:
                # Handle all other types of exceptions
                response = custom_exception_handler(exc, self.get_renderer_context())
                return response
        
        except Exception as e:
            response = custom_exception_handler(exc, self.get_renderer_context())
            return response

class SlackGetChannelsAndUsersAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]
        
    def get(self, request):
        access_token = Slack.objects.get(user=request.user).access_token

        try:
            client = WebClient(token=access_token)
            
            # Fetch list of channels
            response = client.conversations_list(types='private_channel,public_channel')
            channels = response.get('channels', [])
            
            formatted_channels = []

            for channel in channels:
                channel_id = channel.get('id')
                channel_info = {
                    'id': channel_id,
                    'name': channel.get('name'),
                    'is_private': channel.get('is_private'),
                    'num_members': channel.get('num_members'),
                    'members': []
                }

                try:
                    # Fetch members of the channel
                    response = client.conversations_members(channel=channel_id)
                    member_ids = response.get('members', [])

                    for user_id in member_ids:
                        try:
                            # Fetch user info
                            response = client.users_info(user=user_id)
                            user_info = response.get('user', {})
                            
                            channel_info['members'].append({
                                'id': user_id,
                                'name': user_info.get('name', 'Unknown')
                            })

                        except SlackApiError as e:
                            # Handle Slack API-specific errors
                            response = handle_slack_exception(e)
                            return response
                        
                        except Exception as e:
                            # Handle all other types of exceptions
                            response = custom_exception_handler(e, self.get_renderer_context())
                            return response


                except SlackApiError as e:
                    # Handle Slack API-specific errors
                    response = handle_slack_exception(e)
                    return response
                
                except Exception as e:
                    # Handle all other types of exceptions
                    response = custom_exception_handler(e, self.get_renderer_context())
                    return response

                formatted_channels.append(channel_info)

            return Response(formatted_channels, status=status.HTTP_200_OK)

        except SlackApiError as e:
            # Handle Slack API-specific errors
            response = handle_slack_exception(e)
            return response
                
        except Exception as e:
            # Handle all other types of exceptions
            response = custom_exception_handler(e, self.get_renderer_context())
            return response

class MessageChannelView(APIView):
    def get(self,request,id):
        access_token = SlackToken.objects.get(user='demo').token
        headers = {'Authorization': f"Bearer {access_token}",
                   "Content-Type": "application/json; charset=utf-8"
                }
        channel_id = id
        try:
            url = f"https://slack.com/api/conversations.history?channel={channel_id}"
            response = requests.get(url, headers=headers)
            return Response(response.json())
        except:
            return Response({"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self,request,id):
        try:
            message = request.data['message']
            access_token = SlackToken.objects.get(user='demo').token
            headers = {'Authorization': f"Bearer {access_token}",
                       "Content-Type": "application/json; charset=utf-8"
                       }
            channel_id = id
            url = "https://slack.com/api/chat.postMessage"
            url_check = f'https://slack.com/api/conversations.info?channel={channel_id}'
            try:
                response = requests.post(url_check,headers=headers)
                print(response.json())
                if response.json()['channel'].get('is_member') is False:
                    url_join = "https://slack.com/api/conversations.join"
                    data = {
                           "channel": channel_id,
                        }
                    try:
                        response = requests.post(url_join, json=data,headers=headers)
                    except:
                        return Response({"error": "error while joining channel"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                data = {
                    "channel": id,
                    "text": message
                }
                try:
                    response = requests.post(url, headers=headers, json=data).json()
                    return Response({"message": "Message sent successfully","response":response},status=status.HTTP_200_OK)
                except:
                    return Response({"error": "error while sending message"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except:
                return Response({"error": "error while checking whether app is in channel or not"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except:
            return Response({"message":"Bad request"},status=status.HTTP_400_BAD_REQUEST)  

