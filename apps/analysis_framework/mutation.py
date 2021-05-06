import graphene
from django.contrib.auth.models import User
from django.contrib.auth import login

from analysis_framework.models import AnalysisFramework
from analysis_framework.serializers import AnalysisFrameworkSerializer
from analysis_framework.schema import AnalysisFrameworkType
from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    GrapheneMutation,
)


AnalysisFrameworkInputType = generate_input_type_for_serializer(
    'AnalysisFrameworkInputType ',
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
    permission_classes = []
    filterset_class = None


class CreateAnalysisFramework(GrapheneMutation):
    class Arguments:
        data = AnalysisFrameworkInputType(required=True)

    # output fields
    result = graphene.Field(AnalysisFrameworkType)
    # class vars
    serializer_class = AnalysisFrameworkSerializer
    model = AnalysisFramework


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
    login = Login.Field()
