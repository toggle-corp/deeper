from django.contrib.postgres.fields import JSONField, ArrayField
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from user_resource.models import UserResource

from utils.common import random_key


class File(UserResource):
    RANDOM_STRING_LENGTH = 16

    title = models.CharField(max_length=255)

    file = models.FileField(upload_to='gallery/', max_length=255,
                            null=True, blank=True, default=None)
    mime_type = models.CharField(max_length=130, blank=True, null=True)
    metadata = JSONField(default=None, blank=True, null=True)

    is_public = models.BooleanField(default=True)
    projects = models.ManyToManyField('project.Project', blank=True)

    random_string = models.CharField(
        max_length=RANDOM_STRING_LENGTH,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.title

    @staticmethod
    def get_for(user):
        return File.objects.all()
        # return File.objects.filter(
        #     models.Q(created_by=user) |
        #     models.Q(is_public=True) |
        #     models.Q(permitted_users=user) |
        #     models.Q(permitted_user_groups__members=user)
        # ).distinct()

    def can_get(self, user):
        return True
        # return self in File.get_for(user)

    def get_random_string(self):
        if self.random_string is None:
            self.random_string = random_key(File.RANDOM_STRING_LENGTH)
            self.save()
        return self.random_string

    def get_shareable_image_url(self):
        rand_str = self.get_random_string()
        fid = urlsafe_base64_encode(force_bytes(self.pk)).decode()
        return '{protocol}://{domain}{url}'.format(
            protocol=settings.HTTP_PROTOCOL,
            domain=settings.DJANGO_API_HOST,
            url=reverse(
                'gallery_public_url',
                kwargs={
                    'fidb64': fid, 'token': rand_str, 'filename': self.title,
                }
            )
        )

    def can_modify(self, user):
        return self.created_by == user


class FilePreview(models.Model):
    file_ids = ArrayField(models.IntegerField())
    text = models.TextField(blank=True)
    ngrams = JSONField(null=True, blank=True, default=None)
    extracted = models.BooleanField(default=False)

    def __str__(self):
        return 'Text extracted for {}'.format(self.file)
