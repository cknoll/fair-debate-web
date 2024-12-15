from django.db import models
from django.contrib import admin
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

    user_a = models.ForeignKey(
        DebateUser, null=True, on_delete=models.SET_NULL, related_name="debate_as_user_a"
    )
    user_b = models.ForeignKey(
        DebateUser, null=True, on_delete=models.SET_NULL, related_name="debate_as_user_b"
    )

    update_date = models.DateTimeField(auto_now_add=True, null=True)

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

    @staticmethod
    def get_for_user(user: DebateUser, role="all", limit: int = None) -> models.QuerySet:
        """
        result is sorted for "newest first"
        """
        assert role in ("all", "a", "b")

        if role in ("a", "all"):
            res = set_a = Debate.objects.filter(user_a=user)
        if role in ("b", "all"):
            res = set_b = Debate.objects.filter(user_b=user)
        if role == "all":
            res = (set_a | set_b)

        return res.order_by("-update_date")[:limit]

    @staticmethod
    def get_all(limit: int = None) -> models.QuerySet:
        """
        result is sorted for "newest first"
        """

        return Debate.objects.all().order_by("-update_date")[:limit]




class DebateAdmin(admin.ModelAdmin):
    pass


admin.site.register(Debate, DebateAdmin)


class Contribution(models.Model):
    author = models.ForeignKey(DebateUser, on_delete=models.CASCADE)
    debate = models.ForeignKey(Debate, on_delete=models.CASCADE)

    # key like "a" or "a3b24a7b"
    contribution_key = models.CharField(max_length=255)
    body = models.TextField()  # store plain markdown source


class ContributionAdmin(admin.ModelAdmin):
    pass


admin.site.register(Contribution, ContributionAdmin)
