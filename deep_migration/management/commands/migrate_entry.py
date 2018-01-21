from django.core.management.base import BaseCommand

from deep_migration.utils import (
    get_source_url,
    request_with_auth,
)

from deep_migration.models import (
    AnalysisFrameworkMigration,
    ProjectMigration,
    LeadMigration,
    UserMigration,
    CountryMigration,
)
from analysis_framework.models import (
    Filter,
    Exportable,
)
from entry.models import (
    Entry,
    Attribute,
    FilterData,
    ExportData,
)
from geo.models import Region, GeoArea

from datetime import datetime

import reversion


ENTRIES_URL = get_source_url('entries/?template=1', 'v1')
ONE_DAY = 24 * 60 * 60 * 1000


def get_user(old_user_id):
    migration = UserMigration.objects.filter(old_id=old_user_id).first()
    return migration and migration.user


def get_project(project_id):
    migration = ProjectMigration.objects.filter(old_id=project_id).first()
    return migration and migration.project


def get_lead(lead_id):
    migration = LeadMigration.objects.filter(old_id=lead_id).first()
    return migration and migration.lead


def get_analysis_framework(lead_id):
    migration = AnalysisFrameworkMigration.objects.filter(
        old_id=lead_id
    ).first()
    return migration and migration.analysis_framework

def get_region(code):
    migration = CountryMigration.objects.filter(
        code=code
    ).first()
    return migration and migration.region


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        entries = request_with_auth(ENTRIES_URL)

        if not entries:
            print('Couldn\'t find entries data at {}'.format(ENTRIES_URL))

        with reversion.create_revision():
            for entry in entries:
                self.import_entry(entry)

    def import_entry(self, data):
        print('------------')
        print('Migrating entries')

        lead_id = data['lead']
        print('For lead - {}'.format(lead_id))

        lead = get_lead(lead_id)
        if not lead:
            print('Lead not migrated yet')
            return

        lead.entry_set.all().delete()

        framework = None
        project_id = data['event']
        if project_id:
            project = get_project(project_id)
            framework = project.analysis_framework
            regions = project.regions.all()
        else:
            regions = Region.objects.none()

        self.regions = regions

        if not framework:
            template_id = data['template']
            if not template_id:
                print('Not an entry with analysis framework')
                return

            framework = get_analysis_framework(template_id)
            if not framework:
                print('Analysis framework not migrated yet')
                return

        print('Lead title: {}'.format(lead.title))
        informations = data['informations']
        for information in informations:
            self.import_information(data, lead, framework, information)

    def import_information(self, entry_data, lead, framework, data):
        old_id = data['id']
        print('Entry info - {}'.format(old_id))

        entry = Entry(
            lead=lead,
            analysis_framework=framework,
        )

        if data.get('excerpt'):
            entry.excerpt = data['excerpt']
            entry.entry_type = Entry.EXCERPT
        elif data.get('image'):
            entry.image = data['image']
            entry.entry_type = Entry.IMAGE

        entry.created_by = get_user(entry_data['created_by'])
        entry.modified_by = entry.created_by

        entry.save()
        Entry.objects.filter(id=entry.id).update(
            created_at=entry_data['created_at']
        )

        # Start migrating the attributes
        elements = data['elements']
        # TODO migrate excerpt and image widget
        for element in elements:
            self.migrate_attribute(entry, framework, element)

        return entry

    def migrate_attribute(self, entry, framework, element):
        print('Migrating element {}'.format(element['id']))

        widget = framework.widget_set.filter(key=element['id']).first()
        if not widget:
            print('Widget not migrated yet')
            return

        widget_method_map = {
            'numberWidget': self.migrate_number,
            'dateWidget': self.migrate_date,
            'scaleWidget': self.migrate_scale,
            'multiselectWidget': self.migrate_multiselect,
            'organigramWidget': self.migrate_organigram,
            'geoWidget': self.migrate_geo,
        }

        method = widget_method_map.get(widget.widget_id)
        if method:
            method(entry, widget, element)

    def migrate_attribute_data(self, entry, widget, data):
        attribute, _ = Attribute.objects.get_or_create(
            entry=entry,
            widget=widget,
            defaults={
                'data': data,
            },
        )

    def migrate_filter_data(self, entry, widget, number=None, values=None):
        filter = Filter.objects.get(
            widget_key=widget.key,
            analysis_framework=widget.analysis_framework,
        )
        filter_data, _ = FilterData.objects.get_or_create(
            entry=entry,
            filter=filter,
            defaults={
                'number': number,
                'values': values,
            },
        )

    def migrate_export_data(self, entry, widget, data):
        exportable = Exportable.objects.get(
            widget_key=widget.key,
            analysis_framework=widget.analysis_framework,
        )
        export_data, _ = ExportData.objects.get_or_create(
            entry=entry,
            exportable=exportable,
            defaults={
                'data': data,
            },
        )

    def migrate_number(self, entry, widget, element):
        value = element['value'] and int(element['value'])
        self.migrate_attribute_data(entry, widget, {
            'value': value,
        })
        self.migrate_filter_data(entry, widget, number=value)
        self.migrate_export_data(entry, widget, {
            'excel': {
                'value': str(value),
            }
        })

    def migrate_date(self, entry, widget, element):
        value = element['value']
        self.migrate_attribute_data(entry, widget, {
            'value': value,
        })

        date = datetime.strptime(value, '%Y-%m-%d')
        number = int(date.timestamp() / ONE_DAY)
        self.migrate_filter_data(entry, widget, number=number)
        self.migrate_export_data(entry, widget, {
            'excel': {
                'value': date.strftime('%d-%m-%Y'),
            }
        })

    def migrate_scale(self, entry, widget, element):
        value = element.get('value')
        self.migrate_attribute_data(entry, widget, {
            'selectedScale': value,
        })
        self.migrate_filter_data(entry, widget, values=[value])

        widget_data = widget.properties['data']
        scale_units = widget_data['scale_units']
        scale = next((
            s for s in scale_units
            if s['key'] == value
        ), None)
        self.migrate_export_data(entry, widget, {
            'excel': {
                'value': scale['title'] if scale else '',
            }
        })

    def migrate_multiselect(self, entry, widget, element):
        value = element.get('value') or []
        self.migrate_attribute_data(entry, widget, {
            'value': value,
        })
        self.migrate_filter_data(entry, widget, values=value)

        widget_data = widget.properties['data']
        options = widget_data['options']

        label_list = []
        for item in value:
            option = next((
                o for o in options
                if o['key'] == item
            ), None)
            label_list.append(option['label'])

        self.migrate_export_data(entry, widget, {
            'excel': {
                'type': 'list',
                'value': label_list,
            }
        })

    def migrate_organigram(self, entry, widget, element):
        value = element.get('value') or []
        widget_data = widget.properties['data']
        nodes = self.get_organigram_nodes([widget_data], value)

        self.migrate_attribute_data(entry, widget, {
            'values': nodes,
        })
        self.migrate_filter_data(
            entry, widget,
            values=self.get_organigram_filter_data([widget_data], value),
        )

        self.migrate_export_data(entry, widget, {
            'excel': {
                'type': 'list',
                'value': [n['name'] for n in nodes],
            }
        })

    def get_organigram_nodes(self, organs, keys):
        nodes = []
        for organ in organs:
            if organ['key'] in keys:
                nodes.append({
                    'id': organ['key'],
                    'name': organ['title'],
                })

            children = self.get_organigram_nodes(organ['organs'], keys)
            nodes = nodes + children

        return nodes

    def get_organigram_filter_data(self, organs, keys):
        filter_data = []
        for organ in organs:
            children = self.get_organigram_filter_data(organ['organs'], keys)
            if children or organ['key'] in keys:
                filter_data.append(organ['key'])
            filter_data = filter_data + children

        return filter_data

    def migrate_geo(self, entry, widget, element):
        areas = [self.get_geo_area(v) for v in element.get('value', [])]
        values = [
            {
                'key': area.id,
                'label': area.get_label(),
            } for area in areas
        ]
        keys = [v['key'] for v in values]

        self.migrate_attribute_data(entry, widget, {
            'values': values,
        })
        self.migrate_filter_data(
            entry, widget,
            values=keys,
        )

        self.migrate_export_data(entry, widget, {
            'excel': {
                'value': keys,
            }
        })

    def get_geo_area(self, value):
        splits = value.split(':')
        region_code = splits[0]
        admin_level = splits[1]
        area_title = splits[2]
        if len(splits) > 3:
            area_code = splits[3]
        else:
            area_code = None

        region = get_region(region_code)
        if not region or region not in self.regions:
            return None

        areas = GeoArea.objects.filter(
            admin_level__level=admin_level,
            title=area_title,
        )
        if area_code:
            areas = areas.filter(code=area_code)

        return areas.first()
