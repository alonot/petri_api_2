import random

from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.
User=get_user_model()

class Profile(models.Model):
    objects = None

    def generate_CA(self):
        char_list = '1234567890abcdefghijklmnopqrstuvwxyz'
        self.CA = ''.join(random.choice(char_list) for _ in range(6))
    userId=models.IntegerField()
    username = models.CharField(max_length=13)
    email = models.EmailField()
    phone = models.CharField(max_length=13)
    college = models.CharField(max_length=100, null=True)
    year = models.CharField(max_length=5, null=True)
    CA = models.TextField(null=True)

    def __str__(self):
        return self.username
    

class Event(models.Model):
    eventId=models.CharField(max_length=10,default="")
    name=models.CharField(max_length=20,default="")
    about=models.CharField(max_length=300)

class EventTable(models.Model):
    eventId=models.CharField(max_length=10,null=True)
    user_id=models.IntegerField()
    ca_code=models.CharField(max_length=10)
    transactionId=models.CharField(max_length=25)
    verified=models.BooleanField()

