from django.db import models
from django.contrib.auth.models import User

class Debate(models.Model):
    debate_key = models.CharField(max_length=255)

class Contribution(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    debate = models.ForeignKey(Debate, on_delete=models.CASCADE)

    # key like "a" or "a3b24a7b"
    contribution_key = models.CharField(max_length=255)
    body = models.TextField()
