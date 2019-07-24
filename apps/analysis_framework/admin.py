from django.contrib import admin
from analysis_framework.models import (
    AnalysisFramework,
    AnalysisFrameworkRole,
    AnalysisFrameworkMembership,
    Widget, Filter,
    Exportable,
)

from deep.admin import VersionAdmin, StackedInline, query_buttons


class AnalysisFrameworkMemebershipInline(admin.TabularInline):
    model = AnalysisFrameworkMembership
    extra = 0


class WidgetInline(StackedInline):
    model = Widget


class FilterInline(StackedInline):
    model = Filter


class ExportableInline(StackedInline):
    model = Exportable


@admin.register(AnalysisFramework)
class AnalysisFrameworkAdmin(VersionAdmin):
    readonly_fields = ['is_private']
    inlines = [AnalysisFrameworkMemebershipInline]
    search_fields = ('title',)
    custom_inlines = [
        ('widget', WidgetInline),
        ('filter', FilterInline),
        ('exportable', ExportableInline),
    ]
    list_display = [
        'title',  # 'project_count',
        query_buttons('View', [inline[0] for inline in custom_inlines]),
    ]

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        for name, inline in self.custom_inlines:
            if request.GET.get(f'show_{name}', 'False').lower() == 'true':
                inlines.append(inline(self.model, self.admin_site))
        return inlines

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AnalysisFrameworkRole)
class AnalysisFrameworkRoleAdmin(admin.ModelAdmin):
    readonly_fields = ['is_private_role']

    def has_add_permission(self, request, obj=None):
        return False
