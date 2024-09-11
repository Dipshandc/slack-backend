from django.urls import path 
from .views import FileuploadView, GetChannelsAndUsersView, AccessTokenView, MessageChannelView

urlpatterns = [
  path('upload/', FileuploadView.as_view(), name='file_upload'),
  path('channels/', GetChannelsAndUsersView.as_view(), name='channels'),
  path('access-token/', AccessTokenView.as_view(), name='access-token'),
  path('message/<str:id>', MessageChannelView.as_view(), name='message-channel'),
]