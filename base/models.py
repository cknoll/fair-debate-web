from django.db import models
from django.contrib.auth.models import User


# TODO: Obsolete? (Currently not used)
class InitialContribution(models.Model):
    author = User()
    body = models.TextField()


class Contribution(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    debate_key = models.CharField(max_length=255)

    # key like "a" or "a3b24a7b"
    contribution_key = models.CharField(max_length=255)
    body = models.TextField()
