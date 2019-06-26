from django.utils import timezone
from datetime import timedelta
import django_filters
from django.db import models
from rest_framework import (
    exceptions,
    permissions,
    response,
    status,
    filters,
    views,
    viewsets,
)
from deep.permissions import ModifyPermission

from project.models import Project
from entry.models import Entry
from .models import (
    AnalysisFramework, Widget, Filter, Exportable,
    AnalysisFrameworkMembership,
    AnalysisFrameworkRole,
)
from .serializers import (
    AnalysisFrameworkSerializer, WidgetSerializer,
    FilterSerializer, ExportableSerializer,
    AnalysisFrameworkMembershipSerializer,
    AnalysisFrameworkRoleSerializer,
)
from .filter_set import AnalysisFrameworkFilterSet
from .permissions import FrameworkMembershipModifyPermission


class AnalysisFrameworkViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisFrameworkSerializer
    permission_classes = [permissions.IsAuthenticated, ModifyPermission]
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter, filters.OrderingFilter,
    )
    filterset_class = AnalysisFrameworkFilterSet
    search_fields = ('title', 'description',)

    def get_queryset(self):
        query_params = self.request.query_params
        queryset = AnalysisFramework.get_for(self.request.user)
        month_ago = timezone.now() - timedelta(days=30)
        activity_param = query_params.get('activity')

        # Active/Inactive Filter
        if activity_param in ['active', 'inactive']:
            queryset = queryset.annotate(
                recent_entry_exists=models.Exists(
                    Entry.objects.filter(
                        analysis_framework_id=models.OuterRef('id'),
                        modified_at__date__gt=month_ago,
                    )
                ),
            ).filter(
                recent_entry_exists=activity_param.lower() == 'active',
            )

        # Owner Filter
        if query_params.get('relatedToMe', 'false').lower() == 'true':
            queryset = queryset.filter(created_by=self.request.user)
        return queryset


class AnalysisFrameworkCloneView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, af_id, version=None):
        if not AnalysisFramework.objects.filter(
            id=af_id
        ).exists():
            raise exceptions.NotFound()

        analysis_framework = AnalysisFramework.objects.get(
            id=af_id
        )
        if not analysis_framework.can_clone(request.user):
            raise exceptions.PermissionDenied()

        new_af = analysis_framework.clone(
            request.user,
            request.data or {},
        )
        serializer = AnalysisFrameworkSerializer(
            new_af,
            context={'request': request},
        )

        project = request.data.get('project')
        if project:
            project = Project.objects.get(id=project)
            if not project.can_modify(request.user):
                raise exceptions.ValidationError({
                    'project': 'Invalid project',
                })
            project.analysis_framework = new_af
            project.modified_by = request.user
            project.save()

        return response.Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class WidgetViewSet(viewsets.ModelViewSet):
    serializer_class = WidgetSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return Widget.get_for(self.request.user)


class FilterViewSet(viewsets.ModelViewSet):
    serializer_class = FilterSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return Filter.get_for(self.request.user)


class ExportableViewSet(viewsets.ModelViewSet):
    serializer_class = ExportableSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return Exportable.get_for(self.request.user)


class AnalysisFrameworkMembershipViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisFrameworkMembershipSerializer
    permission_classes = [permissions.IsAuthenticated,
                          FrameworkMembershipModifyPermission]

    def get_queryset(self):
        return AnalysisFrameworkMembership.get_for(self.request.user)


class AnalysisFrameworkRoleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AnalysisFrameworkRoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AnalysisFrameworkRole.objects.all()
