from django.db import models

class SlackToken(models.Model):
  user = models.CharField(max_length=255)
  token = models.CharField(max_length=255,null=True,blank=True)

class Channels(models.Model):
  user = models.CharField(max_length=255)
  channel = models.CharField(max_length=255)