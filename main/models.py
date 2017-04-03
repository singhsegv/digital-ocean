from __future__ import unicode_literals

from django.db import models

# Create your models here.

class User(models.Model):
    name = models.CharField(max_length=100, null=True)
    phone = models.CharField(max_length=100, null=True)
    token = models.CharField(max_length=300, null=True)
    email = models.CharField(max_length=100, null=True)
    password = models.CharField(max_length=100, null=True)
