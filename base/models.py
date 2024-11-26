from django.db import models
from django.contrib.auth.models import AbstractUser


class Repo(models.Model):
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=1000)


class DebateUser(AbstractUser):
    repos = models.ManyToManyField(Repo, related_name="users", blank=True)
    active_rep = models.ForeignKey(Repo, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"DebateUser<{self.username}>"


class Debate(models.Model):
    debate_key = models.CharField(max_length=255)
    repo_a = models.ForeignKey(Repo, null=True, on_delete=models.SET_NULL, related_name="debate_a")
    repo_b = models.ForeignKey(Repo, null=True, on_delete=models.SET_NULL, related_name="debate_b")

    user_a = models.ForeignKey(DebateUser, null=True, on_delete=models.SET_NULL, related_name="debate_as_user_a")
    user_b = models.ForeignKey(DebateUser, null=True, on_delete=models.SET_NULL, related_name="debate_as_user_b")

    def get_user_role(self, user: DebateUser):

        if user == self.user_a:
            return "a"
        elif user == self.user_b:
            return "b"
        else:
            return None

    # TODO: take this from metadata
    @property
    def title(self):
        return self.debate_key


class Contribution(models.Model):
    author = models.ForeignKey(DebateUser, on_delete=models.CASCADE)
    debate = models.ForeignKey(Debate, on_delete=models.CASCADE)

    # key like "a" or "a3b24a7b"
    contribution_key = models.CharField(max_length=255)
    body = models.TextField()  # store plain markdown source
