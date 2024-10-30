from django.db import models
from django.contrib.auth.models import User

class InitialContribution(models.Model):
    author = User()
    body = models.TextField()
