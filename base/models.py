from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.db import models


class Repo(models.Model):
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=1000)


class DebateUser(AbstractUser):
    repos = models.ManyToManyField(Repo, related_name="users", blank=True)
    active_rep = models.ForeignKey(Repo, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"DebateUser<{self.username}>"


class Debate(models.Model):
    class Discoverability(models.TextChoices):
        PUBLIC = "public", "Public"
        HIDDEN = "hidden", "Hidden"
        PRIVATE = "private", "Private"

    debate_key = models.CharField(max_length=255)  # TODO: add unique=True
    repo_a = models.ForeignKey(Repo, null=True, on_delete=models.SET_NULL, related_name="debate_a")
    repo_b = models.ForeignKey(Repo, null=True, on_delete=models.SET_NULL, related_name="debate_b")

    user_a = models.ForeignKey(
        DebateUser, null=True, on_delete=models.SET_NULL, related_name="debate_as_user_a"
    )
    user_b = models.ForeignKey(
        DebateUser, null=True, on_delete=models.SET_NULL, related_name="debate_as_user_b"
    )

    update_date = models.DateTimeField(auto_now=True)

    # this will be 1, if an a-contribution is committed etc.
    n_committed_contributions = models.IntegerField(default=0)

    discoverability = models.CharField(
        # note: the default value is used elsewhere, e.g. in views.py
        max_length=20, choices=Discoverability.choices, default=Discoverability.PUBLIC
    )

    # this field serves to introduce a database change to test/debug the effect of db changes in deployment
    # currently needed to reuse backups
    # irrelevant_attribute = models.IntegerField(default=0)

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
            res = set_a | set_b

        return res.order_by("-update_date")[:limit]

    @staticmethod
    def get_all(limit: int = None, exclude_uncommitted=True) -> models.QuerySet:
        """
        result is sorted for "newest first"
        """
        if exclude_uncommitted:
            return Debate.objects.filter(n_committed_contributions__gt=0).order_by("-update_date")[:limit]
        else:
            return Debate.objects.all().order_by("-update_date")[:limit]

    def __str__(self):
        return f"Debate<{self.debate_key}>"




class DebateAsUserAInline(admin.TabularInline):
    model = Debate
    fk_name = "user_a"
    extra = 0
    readonly_fields = ["debate_key", "repo_a", "repo_b", "user_b", "update_date", "n_committed_contributions", "discoverability"]


class DebateAsUserBInline(admin.TabularInline):
    model = Debate
    fk_name = "user_b"
    extra = 0
    readonly_fields = ["debate_key", "repo_a", "repo_b", "user_a", "update_date", "n_committed_contributions", "discoverability"]


class DebateAdmin(admin.ModelAdmin):
    pass


class DebateUserAdmin(admin.ModelAdmin):
    inlines = [DebateAsUserAInline, DebateAsUserBInline]


admin.site.register(DebateUser, DebateUserAdmin)
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
