from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from dotenv import load_dotenv
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from io import BytesIO
from .models import SlackToken
from .slack_exceptions import handle_slack_exception
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

class GetChannelsAndUsersView(APIView):
    def get(self, request):
        url1 = "https://slack.com/api/conversations.list"
        query_params = {
        'types': 'private_channel,public_channel',
        }
        access_token = SlackToken.objects.get(user='demo').token
        headers = {

        "Authorization": f"Bearer {access_token}"
        
        }
        try:
            response = requests.get(url1, params=query_params,headers=headers )
            response.raise_for_status()
            channels = response.json()
            
            formatted_channels = []
            print(channels)
            for channel in channels['channels']:
                print(channel)
                channel_id = channel['id']
                channel_info = {
                    'id': channel_id,
                    'name': channel['name'],
                    'is_private': channel['is_private'],
                    'num_members': channel['num_members'],
                    'members': []
                }
                try:
                    url2 = "https://slack.com/api/conversations.members"
                    headers = {
                    "Authorization": f"Bearer {access_token}"
                    }

                    params = {
                          "channel": channel_id
                    }
                    response = requests.get(url2, headers=headers, params=params)
                    member_ids = response.json()
                    print(member_ids)
                    for user_id in member_ids['members']:
                        try:
                            url3 = f"https://slack.com/api/users.info?user={user_id}"
                            headers = {
                             "Authorization": f"Bearer {access_token}"
                            }

                            response = requests.get(url3, headers=headers)
                            user_info = response.json()
                            print(user_info)
                        except:
                            return Response("Error getting users")
                        
                        channel_info['members'].append({
                            'id': user_id,
                            'name': user_info['user']['name'],
                        })
                
                except SlackApiError as e:
                    # If we can't get members, just note the error and continue
                    channel_info['members'] = f"Error fetching members: {e.response['error']}"
                
                formatted_channels.append(channel_info)
            
            return Response(formatted_channels, status=status.HTTP_200_OK)
        
        except SlackApiError as e:
            error_message = f"Error fetching data: {e.response['error']}"
            return Response({"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AccessTokenView(APIView):
    def post(self,request):
        print(request.data)
        try:
            print(request.data)
            access_token = request.data['access']
            print(access_token)
            slack_token, created = SlackToken.objects.get_or_create(user='demo')
            print(slack_token)
            slack_token.token = access_token
            slack_token.save()     
            return Response({"message": "Access token saved successfully"}, status=status.HTTP_200_OK)
        except:
            return Response({"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)


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

