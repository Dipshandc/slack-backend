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

class SlackSaveAccessTokenAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self,request):
        try:
            access_token = request.data['access']
            slack_token, created = SlackToken.objects.get_or_create(user=request.user)
            slack_token.token = access_token
            slack_token.save()     
            return Response({"message": "Access token saved successfully"}, status=status.HTTP_200_OK)
        
        except Exception as exc:
            response = custom_exception_handler(exc, self.get_renderer_context())
            return response

class SlackCheckConnectionAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        ]
    
    def get(self, request):

        try:
            access_token = Slack.objects.get(user=request.user).access_token
            print(access_token)
            client = WebClient(token=access_token)
            response = client.team_info()
            if response['ok']:
                data = {
                    "workspace":response['team']['name'],
                    "icon":response['team']['icon']['image_34']
                }
                return Response({"status":True,"data":data},status=status.HTTP_200_OK)
            else:
                return Response({"status":False,"message":"Slack connection failed"},status=status.HTTP_200_OK)
        
        except SlackApiError as e:
            # Handle Slack API-specific errors
            return handle_slack_exception(e)

        except Exception as exc:
            # Handle all other types of exceptions
            return custom_exception_handler(exc, self.get_renderer_context())
        
class SlackFileUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            access_token = SlackToken.objects.get(user=request.user).access_token
            channel_id = request.data['channel_id']
            message = request.data['message']
            file = request.data['file']
            file_bytes = file.read()
            file_io = BytesIO(file_bytes)
            client = WebClient(token=access_token)

            # Check if the app is a member of the channel
            response = client.conversations_info(channel=channel_id)
            if not response['channel'].get('is_member'):
                # Join the channel if not already a member
                client.conversations_join(channel=channel_id)

            # Upload the file
            client.files_upload_v2(channel=channel_id, file=file_io, initial_comment=message)

            return Response({"message": "File uploaded successfully"}, status=status.HTTP_200_OK)

        except SlackApiError as e:
            # Handle SlackToken API-specific errors
            return handle_slack_exception(e)

        except Exception as exc:
            # Handle all other types of exceptions
            return custom_exception_handler(exc, self.get_renderer_context())

class SlackGetChannelsAndUsersAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]
        
    def get(self, request):
        try:
            access_token = SlackToken.objects.get(user=request.user).access_token
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

                # Fetch members of the channel
                response = client.conversations_members(channel=channel_id)
                member_ids = response.get('members', [])

                for user_id in member_ids:
                    # Fetch user info
                    response = client.users_info(user=user_id)
                    user_info = response.get('user', {})
                            
                    channel_info['members'].append({
                        'id': user_id,
                        'name': user_info.get('name', 'Unknown')
                    })

                formatted_channels.append(channel_info)

            return Response(formatted_channels, status=status.HTTP_200_OK)

        except SlackApiError as e:
            # Handle SlackToken API-specific errors
            response = handle_slack_exception(e)
            return response
                
        except Exception as e:
            # Handle all other types of exceptions
            response = custom_exception_handler(e, self.get_renderer_context())
            return response
        
class MessageChannelView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, id):
        try:
            access_token = SlackToken.objects.get(user=request.user).token
            client = WebClient(token=access_token)
            channel_id = id
            
            # Fetch channel message history
            response = client.conversations_history(channel=channel_id)
            return Response(response.data, status=status.HTTP_200_OK)

        except SlackApiError as e:
            # Handle SlackToken API-specific errors
            response = handle_slack_exception(e)
            return response

        except Exception as exc:
            # Handle all other types of exceptions
            response = custom_exception_handler(exc, self.get_renderer_context())
            return response

    def post(self, request, id):
        try:
            message = request.data.get('message')
            access_token = SlackToken.objects.get(user=request.user).token
            client = WebClient(token=access_token)
            channel_id = id

            # Check if the app is a member of the channel
            response = client.conversations_info(channel=channel_id)

            if not response['channel'].get('is_member'):
                # Join the channel if not already a member
                client.conversations_join(channel=channel_id)
               
            response = client.chat_postMessage(channel=channel_id, text=message)
            return Response({"message": "Message sent successfully", "response": response.data}, status=status.HTTP_200_OK)

        except SlackApiError as e:
            # Handle SlackToken API-specific errors
            response = handle_slack_exception(e)
            return response

        except Exception as exc:
            # Handle all other types of exceptions
            response = custom_exception_handler(exc, self.get_renderer_context())
            return response

class SlackDisconnetAPIView(APIView):
    def post(self, request):
        try:
            slack = SlackToken.objects.get(user=request.user)
            slack.delete()
            return Response({"status":True,"message":f'Slack successfully disconnected for {request.user}'},status=status.HTTP_200_OK)

        except Exception as exc:
            response = custom_exception_handler(exc, self.get_renderer_context())
            return response