from django.urls import path 
from .views import *

urlpatterns = [
  path('upload/', SlackFileUploadAPIView.as_view(), name='file_upload'),
  path('channels/', SlackGetChannelsAndUsersAPIView.as_view(), name='channels'),
  path('access-token/', SlackSaveAccessTokenAPIView.as_view(), name='access-token'),
  path('message/<str:id>', MessageChannelView.as_view(), name='message-channel'),
  path('disconnect-slack/', SlackDisconnetAPIView.as_view(), name='message-channel'),
  
]