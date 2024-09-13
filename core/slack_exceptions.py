from rest_framework.response import Response
from rest_framework import status
from slack_sdk.errors import SlackApiError

def handle_slack_exception(e:SlackApiError):
  custom_response = {
    "status": e.response['ok'],
    "code": e.response.status_code,
    "message": e.response['error'],
  }
  return Response(custom_response,status=status.HTTP_400_BAD_REQUEST)
