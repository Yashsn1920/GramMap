from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin"
        REVIEWER = "reviewer"
        VIEWER = "viewer"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.VIEWER)


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=40)
    object_type = models.CharField(max_length=60)
    object_id = models.CharField(max_length=60)
    diff = models.JSONField(default=dict, blank=True)
    at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.at:%Y-%m-%d %H:%M} {self.action} {self.object_type}:{self.object_id}"
