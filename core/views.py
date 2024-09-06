from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from dotenv import load_dotenv
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from io import BytesIO
from .models import SlackToken
import requests

load_dotenv()

class FileuploadView(APIView):
    def post(self, request):

        access_token = SlackToken.objects.get(user='demo').token
        try:
         client = WebClient(token=access_token)
        except:
            return Response({"error": "Invalid access token"}, status=status.HTTP_400_BAD_REQUEST)

        try:
          print(request.data['message'])
          message = request.data['message']
          channel = request.data['channel_id']
          print(channel)
          file = request.data['file']
          print(file)
          file_bytes = file.read()
          file_io = BytesIO(file_bytes)
          try:
            client.files_upload_v2(
               channel=channel,
               file=file_io,
               initial_comment=message
            )
          except SlackApiError:
              return Response({"error": "Failed to upload file"},SlackApiError, status=status.HTTP_400_BAD_REQUEST)
          print("gg")
          return Response({"message": "File uploaded successfully"},status=status.HTTP_200_OK)
    
        except:
           return Response({"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)

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

