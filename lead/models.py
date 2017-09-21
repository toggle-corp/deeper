from django.contrib.auth.models import User
from django.db import models
from project.models import Project
from user_resource.models import UserResource


class Lead(UserResource):
    # Confidentiality choices
    UNPROTECTED = 'unprotected'
    PROTECTED = 'protected'
    RESTRICTED = 'restricted'
    CONFIDENTIAL = 'confidential'

    CONFIDENTIALITIES = (
        (UNPROTECTED, 'Unprotected'),
        (PROTECTED, 'Protected'),
        (RESTRICTED, 'Restricted'),
        (CONFIDENTIAL, 'Confidential'),
    )

    # Status of a lead that can be pending, processed or deleted.
    PENDING = 'pending'
    PROCESSED = 'processed'
    DELETED = 'deleted'

    STATUSES = (
        (PENDING, 'Pending'),
        (PROCESSED, 'Processed'),
        (DELETED, 'Deleted'),
    )

    project = models.ForeignKey(Project)
    title = models.CharField(max_length=255)
    source = models.CharField(max_length=255, blank=True)

    confidentiality = models.CharField(max_length=30,
                                       choices=CONFIDENTIALITIES,
                                       default=UNPROTECTED)
    status = models.CharField(max_length=30,
                              choices=STATUSES,
                              default=PENDING)

    assignee = models.ManyToManyField(User, blank=True)
    published_on = models.DateField(default=None, null=True, blank=True)

    text = models.TextField(blank=True)
    url = models.CharField(max_length=255, blank=True)
    website = models.CharField(max_length=255, blank=True)

    attachment = models.FileField(upload_to='lead_attachments/%Y/%m/',
                                  default=None, null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.title)
