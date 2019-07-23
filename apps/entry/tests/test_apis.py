from deep.tests import TestCase
import autofixture

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from project.models import Project
from user.models import User
from lead.models import Lead
from analysis_framework.models import (
    AnalysisFramework, Widget, Filter
)
from entry.models import (
    Entry,
    Attribute,
    FilterData,
)

from gallery.models import File
from tabular.models import Sheet, Field


class EntryTests(TestCase):
    def create_entry_with_data_series(self):
        sheet = autofixture.create_one(Sheet, generate_fk=True)
        series = [  # create some dummy values
            {
                'value': 'male', 'processed_value': 'male',
                'invalid': False, 'empty': False
            },
            {
                'value': 'female', 'processed_value': 'female',
                'invalid': False, 'empty': False
            },
            {
                'value': 'female', 'processed_value': 'female',
                'invalid': False, 'empty': False
            },
        ]
        cache_series = [
            {'value': 'male', 'count': 1},
            {'value': 'female', 'count': 2},
        ]
        health_stats = {
            'invalid': 10,
            'total': 20,
            'empty': 10,
        }

        field = autofixture.create_one(
            Field,
            field_values={
                'sheet': sheet,
                'title': 'Abrakadabra',
                'type': Field.STRING,
                'data': series,
                'cache': {
                    'status': Field.CACHE_SUCCESS,
                    'series': cache_series,
                    'health_stats': health_stats,
                    'images': [],
                },
            }
        )

        entry = self.create_entry(
            tabular_field=field, entry_type=Entry.DATA_SERIES
        )
        return entry, field

    def test_create_entry(self):
        entry_count = Entry.objects.count()

        lead = self.create_lead()
        widget = self.create(
            Widget,
            analysis_framework=lead.project.analysis_framework,
        )

        url = '/api/v1/entries/'
        data = {
            'lead': lead.pk,
            'project': lead.project.pk,
            'analysis_framework': widget.analysis_framework.pk,
            'excerpt': 'This is test excerpt',
            'attributes': {
                widget.pk: {
                    'data': {'a': 'b'},
                },
            },
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        r_data = response.json()
        self.assertEqual(Entry.objects.count(), entry_count + 1)
        self.assertEqual(r_data['versionId'], 1)
        self.assertEqual(r_data['excerpt'], data['excerpt'])

        attributes = r_data['attributes']
        self.assertEqual(len(attributes.values()), 1)

        attribute = Attribute.objects.get(
            id=attributes[str(widget.pk)]['id']
        )

        self.assertEqual(attribute.widget.pk, widget.pk)
        self.assertEqual(attribute.data['a'], 'b')

        # Check if project matches
        entry = Entry.objects.get(id=r_data['id'])
        self.assertEqual(entry.project, entry.lead.project)

    def test_create_entry_no_project(self):
        entry_count = Entry.objects.count()
        lead = self.create_lead()

        widget = self.create(
            Widget,
            analysis_framework=lead.project.analysis_framework,
        )

        url = '/api/v1/entries/'
        data = {
            'lead': lead.pk,
            'analysis_framework': widget.analysis_framework.pk,
            'excerpt': 'This is test excerpt',
            'attributes': {
                widget.pk: {
                    'data': {'a': 'b'},
                },
            },
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        r_data = response.json()
        self.assertEqual(Entry.objects.count(), entry_count + 1)
        self.assertEqual(r_data['versionId'], 1)
        self.assertEqual(r_data['excerpt'], data['excerpt'])

        attributes = r_data['attributes']
        self.assertEqual(len(attributes.values()), 1)

        attribute = Attribute.objects.get(
            id=attributes[str(widget.pk)]['id']
        )

        self.assertEqual(attribute.widget.pk, widget.pk)
        self.assertEqual(attribute.data['a'], 'b')

        # Check if project matches
        entry = Entry.objects.get(id=r_data['id'])
        self.assertEqual(entry.project, entry.lead.project)

    def test_create_entry_no_perm(self):
        entry_count = Entry.objects.count()

        lead = self.create_lead()
        widget = self.create(
            Widget,
            analysis_framework=lead.project.analysis_framework,
        )

        user = self.create(User)
        lead.project.add_member(user, self.view_only_role)

        url = '/api/v1/entries/'
        data = {
            'lead': lead.pk,
            'project': lead.project.pk,
            'analysis_framework': widget.analysis_framework.pk,
            'excerpt': 'This is test excerpt',
            'attributes': {
                widget.pk: {
                    'data': {'a': 'b'},
                },
            },
        }

        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_403(response)

        self.assertEqual(Entry.objects.count(), entry_count)

    def test_delete_entry(self):
        entry = self.create_entry()

        url = '/api/v1/entries/{}/'.format(entry.id)

        self.authenticate()

        response = self.client.delete(url)
        self.assert_204(response)

    def test_delete_entry_no_perm(self):
        entry = self.create_entry()
        user = self.create(User)
        entry.project.add_member(user, self.view_only_role)

        url = '/api/v1/entries/{}/'.format(entry.id)

        self.authenticate(user)

        response = self.client.delete(url)
        self.assert_403(response)

    def test_duplicate_entry(self):
        entry_count = Entry.objects.count()
        lead = self.create_lead()

        client_id = 'randomId123'
        url = '/api/v1/entries/'
        data = {
            'lead': lead.pk,
            'project': lead.project.pk,
            'excerpt': 'Test excerpt',
            'analysis_framework': lead.project.analysis_framework.id,
            'client_id': client_id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        r_data = response.json()
        self.assertEqual(Entry.objects.count(), entry_count + 1)
        self.assertEqual(r_data['clientId'], client_id)
        id = r_data['id']

        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Entry.objects.count(), entry_count + 1)
        self.assertEqual(r_data['id'], id)
        self.assertEqual(r_data['clientId'], client_id)

    def test_patch_attributes(self):
        entry = self.create_entry()
        widget1 = self.create(
            Widget,
            analysis_framework=entry.lead.project.analysis_framework,
        )
        widget2 = self.create(
            Widget,
            analysis_framework=entry.lead.project.analysis_framework,
        )
        self.create(
            Attribute,
            data={'a': 'b'},
            widget=widget1,
        )

        url = '/api/v1/entries/{}/'.format(entry.id)
        data = {
            'attributes': {
                widget1.pk: {
                    'data': {'c': 'd'},
                },
                widget2.pk: {
                    'data': {'e': 'f'},
                }
            },
        }

        self.authenticate()
        response = self.client.patch(url, data)
        self.assert_200(response)

        r_data = response.json()
        attributes = r_data['attributes']
        self.assertEqual(len(attributes.values()), 2)

        attribute1 = attributes[str(widget1.pk)]
        self.assertEqual(attribute1['data']['c'], 'd')
        attribute2 = attributes[str(widget2.pk)]
        self.assertEqual(attribute2['data']['e'], 'f')

    def test_options(self):
        url = '/api/v1/entry-options/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

    def filter_test(self, params, count=1):
        url = '/api/v1/entries/?{}'.format(params)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        r_data = response.json()
        self.assertEqual(len(r_data['results']), count)

    def post_filter_test(self, filters, count=1):
        url = '/api/v1/entries/filter/'
        params = {
            'filters': [[k, v] for k, v in filters.items()]
        }

        self.authenticate()
        response = self.client.post(url, params)
        self.assert_200(response)

        r_data = response.json()
        self.assertEqual(len(r_data['results']), count)

    def both_filter_test(self, filters, count=1):
        self.filter_test(filters, count)

        k, v = filters.split('=')
        filters = {k: v}
        self.post_filter_test(filters, count)

    def test_filters(self):
        entry = self.create_entry()

        filter = self.create(
            Filter,
            analysis_framework=entry.analysis_framework,
            widget_key='test_filter',
            key='test_filter',
            title='Test Filter',
            filter_type=Filter.NUMBER,
        )
        self.create(FilterData, entry=entry, filter=filter, number=500)

        self.both_filter_test('test_filter=500')
        self.both_filter_test('test_filter__lt=600')
        self.both_filter_test('test_filter__gt=400')
        self.both_filter_test('test_filter__lt=400', 0)

        filter = self.create(
            Filter,
            analysis_framework=entry.analysis_framework,
            widget_key='test_list_filter',
            key='test_list_filter',
            title='Test List Filter',
            filter_type=Filter.LIST,
        )
        self.create(FilterData, entry=entry, filter=filter,
                    values=['abc', 'def', 'ghi'])

        self.both_filter_test('test_list_filter=abc')
        self.both_filter_test('test_list_filter=ghi,def', 1)
        self.both_filter_test('test_list_filter=uml,hij', 0)

        entry.excerpt = 'hello'
        entry.save()
        self.post_filter_test({'search': 'el'}, 1)
        self.post_filter_test({'search': 'pollo'}, 0)

    def test_search_filter(self):
        entry, field = self.create_entry_with_data_series()
        filters = {
            'search': 'kadabra'
        }
        self.post_filter_test(filters)  # Should have single result

    # TODO: test export data and filter data apis


class EntryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.file = File.objects.create(title='test')

    def create_project(self):
        analysis_framework = self.create(AnalysisFramework)
        return self.create(
            Project, analysis_framework=analysis_framework,
            role=self.admin_role
        )

    def create_lead(self):
        project = self.create_project()
        return self.create(Lead, project=project)

    def create_entry(self, **fields):
        lead = self.create_lead()
        return self.create(
            Entry, lead=lead, project=lead.project,
            analysis_framework=lead.project.analysis_framework,
            **fields
        )

    def test_entry_no_image(self):
        entry = self.create_entry(image='')
        assert entry.get_shareable_image_url() is None

    def test_entry_image(self):
        entry_image_url = '/some/path'
        entry = self.create_entry(
            image='{}/{}'.format(entry_image_url, self.file.id)
        )
        assert entry.get_shareable_image_url() is not None
        # Get file again, because it won't have random_string updated
        file = File.objects.get(id=self.file.id)
        assert entry.get_shareable_image_url() == '{protocol}://{domain}{url}'.format(
            protocol=settings.HTTP_PROTOCOL,
            domain=settings.DJANGO_API_HOST,
            url='/public-file/{fidb64}/{token}/{filename}'.format(**{
                'fidb64': urlsafe_base64_encode(force_bytes(file.pk)).decode(),
                'token': file.get_random_string(),
                'filename': file.title,
            }
            ),
        )
