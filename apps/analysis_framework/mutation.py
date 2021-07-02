import graphene
from django.contrib.auth.models import User
from django.contrib.auth import login
from rest_framework import permissions

from analysis_framework.models import AnalysisFramework
from analysis_framework.serializers import (
    AnalysisFrameworkSerializer,
)
from analysis_framework.schema import AnalysisFrameworkType
from deep.permissions import ModifyPermission
from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    GrapheneMutation,
    DeleteMutation,
)


AnalysisFrameworkInputType = generate_input_type_for_serializer(
    'AnalysisFrameworkInputType',
    serializer_class=AnalysisFrameworkSerializer
)


class UpdateAnalysisFramework(GrapheneMutation):
    class Arguments:
        data = AnalysisFrameworkInputType(required=True)
        id = graphene.ID(required=True)

    result = graphene.Field(AnalysisFrameworkType)
    # class vars
    serializer_class = AnalysisFrameworkSerializer
    model = AnalysisFramework
    permission_classes = [permissions.IsAuthenticated, ModifyPermission]


class CreateAnalysisFramework(GrapheneMutation):
    class Arguments:
        data = AnalysisFrameworkInputType(required=True)

    # output fields
    result = graphene.Field(AnalysisFrameworkType)
    # class vars
    serializer_class = AnalysisFrameworkSerializer
    model = AnalysisFramework
    permission_classes = [permissions.IsAuthenticated, ModifyPermission]


class DeleteAnalysisFramework(DeleteMutation):
    class Arguments:
        id = graphene.ID(required=True)

    # output fields
    result = graphene.Field(AnalysisFrameworkType)
    # class vars
    model = AnalysisFramework
    permission_classes = [permissions.IsAuthenticated, ModifyPermission]


class Login(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)

    ok = graphene.Boolean()

    @staticmethod
    def mutate(root, info, email):
        user = User.objects.get(email=email)
        login(info.context.request, user)
        return Login(ok=True)


class Mutation(object):
    create_analysis_framework = CreateAnalysisFramework.Field()
    update_analysis_framework = UpdateAnalysisFramework.Field()
    delete_analysis_framework = DeleteAnalysisFramework.Field()
    login = Login.Field()
