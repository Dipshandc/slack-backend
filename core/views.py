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
        IsAuthenticated,IsOrganizationAdminUser
    ]

    def post(self,request):
        try:
            access_token = request.data['access']
            organization = Organization.objects.first()
            slack, created =  SlackToken.objects.get_or_create(organization=organization)
            slack.access_token = access_token
            slack.save()     
            return Response({"status": True,"message": "Access token saved successfully"}, status=status.HTTP_200_OK)
    
        except SlackApiError as e:
            # Handle Slack API-specific errors
            return handle_slack_exception(e)

        except Exception as exc:
            # Handle all other types of exceptions
            return custom_exception_handler(exc, self.get_renderer_context())
    
class SlackCheckConnectionAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        ]
    
    def get(self, request):

        try:
            organization = Organization.objects.first()
            slack = SlackToken.objects.get(organization=organization)
            if slack is not None:
                client = WebClient(token=slack.access_token)
                response = client.team_info()
                if response['ok']:
                    data = {
                        "workspace":response['team']['name'],
                        "icon":response['team']['icon']['image_34']
                    }
                    return Response({"status":True,"data":data},status=status.HTTP_200_OK)
                else:
                    return Response({"status":False,"message":"Slack connection failed"},status=status.HTTP_200_OK)
            else:
                return Response({"status":False,"message":"Slack not connected"},status=status.HTTP_200_OK)
            
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
            organization = Organization.objects.first()
            slack = SlackToken.objects.get(organization=organization)
            if slack is not None:
                access_token = slack.access_token
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
            else:
                return Response({"staus":False,"message":"Slack not connected"})
            
        except SlackApiError as e:
            # Handle Slack API-specific errors
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
            organization = Organization.objects.first()
            slack = SlackToken.objects.get(organization=organization)
            if slack is not None:
                access_token = slack.access_token
                client = WebClient(token=access_token)
                
                # Fetch list of channels
                response = client.conversations_list(types='private_channel,public_channel')
                channels = response.get('channels', [])
                
                formatted_channels = []

                for channel in channels:
                    channel_id = channel.get('id')
                    selected_channel_exists = SlackSelectedChannel.objects.filter(channel_id=channel_id).exists()
                    if selected_channel_exists:
                        channel_info = {
                            'hrefid': channel_id,
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
                                'name': user_info.get('real_name', 'Unknown')
                            })

                        formatted_channels.append(channel_info)

                return Response(formatted_channels, status=status.HTTP_200_OK)
            
            else:
                return Response({"staus":False,"message":"Slack not connected"})
            
        except SlackApiError as e:
            # Handle Slack API-specific errors
            response = handle_slack_exception(e)
            return response
                
        except Exception as e:
            # Handle all other types of exceptions
            response = custom_exception_handler(e, self.get_renderer_context())
            return response
        
class SlackSendMessageAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, id):
        try:
            organization = Organization.objects.first()
            slack = Slack.objects.get(organization=organization)
            if slack is not None:
                access_token = slack.access_token
                client = WebClient(token=access_token)
                channel_id = id
                
                # Fetch channel message history
                response = client.conversations_history(channel=channel_id)
                return Response(response.data, status=status.HTTP_200_OK)
            
            else:
                return Response({"staus":False,"message":"Slack not connected"})
            
        except SlackApiError as e:
            # Handle Slack API-specific errors
            response = handle_slack_exception(e)
            return response

        except Exception as exc:
            # Handle all other types of exceptions
            response = custom_exception_handler(exc, self.get_renderer_context())
            return response

    def post(self, request, id):
        try:
            message = request.data.get('text')
            organization = Organization.objects.first()
            slack = Slack.objects.get(organization=organization)
            if slack is not None:
                access_token = slack.access_token
                client = WebClient(token=access_token)
                channel_id = id

                # Check if the app is a member of the channel
                response = client.conversations_info(channel=channel_id)

                if not response['channel'].get('is_member'):
                    # Join the channel if not already a member
                    client.conversations_join(channel=channel_id)
                
                response = client.chat_postMessage(channel=channel_id, text=message)
                return Response({"message": "Message sent successfully", "status": True}, status=status.HTTP_200_OK)
            
            else:
                return Response({"staus":False,"message":"Slack not connected"})
            
        except SlackApiError as e:
            # Handle Slack API-specific errors
            response = handle_slack_exception(e)
            return response

        except Exception as exc:
            # Handle all other types of exceptions
            response = custom_exception_handler(exc, self.get_renderer_context())
            return response
        
class SlackDisconnetAPIView(APIView):
    def post(self, request):
        try:
            organization = Organization.objects.first()
            slack = Slack.objects.get(organization=organization)
            if slack is not None:
                slack.access_token = None
                slack.save()
                return Response({"status":True,"message":f'Slack successfully disconnected for {request.user}'},status=status.HTTP_200_OK)
            else:
                return Response({"staus":False,"message":"Slack not connected"})
            
        except Exception as exc:
            response = custom_exception_handler(exc, self.get_renderer_context())
            return response

class SlackSelectedChannelGetOrUpdateAPIView(APIView):

    permission_classes = [IsAuthenticated,IsOrganizationAdminUser]

    def get(self,request):
        try:
            slack = Slack.objects.first()
            if slack is not None:
                selected_channels = SlackSelectedChannel.objects.values_list('channel_id', flat=True)
                selected_channel_ids = list(selected_channels)
                access_token = slack.access_token
                client = WebClient(token=access_token)
                channels = client.conversations_list()
                channels_list = channels['channels']
                formated_selected_channel_list = []

                for channel in channels_list:
                    formated_selected_channel_list.append({
                        'id': channel['id'],
                        'name': channel['name'],
                        'is_selected': channel['id'] in selected_channel_ids
                    })

                    response = {
                        'satus':True,
                        'message':'Channels list successfully fetched',
                        'channels':formated_selected_channel_list
                    }

                return Response(response,status=status.HTTP_200_OK)
                
            else:
                return Response({"staus":False,"message":"Slack not connected"})
            
        except SlackApiError as e:
            # Handle Slack API-specific errors
            response = handle_slack_exception(e)
            return response

        except Exception as exc:
            # Handle all other types of exceptions
            response = custom_exception_handler(exc, self.get_renderer_context())
            return response
        
    def post(self,request):
        try:
            slack = Slack.objects.first() 
            updated_selected_channels = request.data  # Channels sent from the frontend
            
            # Get all existing SlackSelectedChannel objects for the current Slack
            existing_channels = SlackSelectedChannel.objects.filter(slack=slack)
            
            # Extract channel_ids from the updated list
            updated_channel_ids = [channel.get('channel_id') for channel in updated_selected_channels]
            
            # Delete channels that exist in the database but are not in the updated list
            existing_channel_ids = existing_channels.values_list('channel_id', flat=True)
            channels_to_delete = existing_channels.exclude(channel_id__in=updated_channel_ids)
            channels_to_delete.delete()
            
            # Create new channels if they don't already exist
            for channel in updated_selected_channels:
                slack_exists = SlackSelectedChannel.objects.filter(slack=slack, channel_id=channel.get('channel_id')).exists()
                if not slack_exists:
                    SlackSelectedChannel.objects.create(slack=slack, channel_id=channel.get('channel_id'))
            
            response = {
                'status': True,
                'message': 'Selected Channels updated successfully'
            }
            return Response(response, status=status.HTTP_200_OK)
            
        except SlackApiError as e:
            # Handle Slack API-specific errors
            response = handle_slack_exception(e)
            return response

        except Exception as exc:
            # Handle all other types of exceptions
            response = custom_exception_handler(exc, self.get_renderer_context())
            return response


