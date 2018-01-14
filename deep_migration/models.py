from django.contrib.auth.models import User
from django.db import models
from geo.models import (
    Region,
    AdminLevel,
)
from project.models import Project


class BaseMigration(models.Model):
    first_migrated_at = models.DateTimeField(auto_now_add=True)
    last_migrated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-first_migrated_at']


class UserMigration(models.Model):
    old_id = models.IntegerField(unique=True)
    user = models.ForeignKey(User,
                             default=None, blank=True, null=True)


class CountryMigration(BaseMigration):
    code = models.CharField(max_length=50, unique=True)
    region = models.ForeignKey(Region,
                               default=None, blank=True, null=True)


class AdminLevelMigration(BaseMigration):
    old_id = models.IntegerField(unique=True)
    admin_level = models.ForeignKey(AdminLevel,
                                    default=None, blank=True, null=True)


class ProjectMigration(BaseMigration):
    old_id = models.IntegerField(unique=True)
    project = models.ForeignKey(Project,
                                default=None, blank=True, null=True)
