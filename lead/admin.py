from django.contrib import admin
from reversion.admin import VersionAdmin
from .models import (
    Lead, LeadGroup,
    LeadPreview, LeadPreviewImage,
)


class LeadPreviewInline(admin.StackedInline):
    model = LeadPreview


class LeadPreviewImageInline(admin.TabularInline):
    model = LeadPreviewImage


@admin.register(Lead)
class LeadAdmin(VersionAdmin):
    inlines = [LeadPreviewInline, LeadPreviewImageInline]


@admin.register(LeadGroup)
class LeadGroupAdmin(VersionAdmin):
    pass
