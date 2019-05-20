from geo.models import GeoArea


def get_locations_info(assessment):
    locations = assessment.methodology['locations']

    geo_areas = GeoArea.objects.filter(id__in=locations).prefetch_related('admin_level', 'parent')
    admin_levels = {f'Admin {x+1}': [] for x in range(6)}

    if not geo_areas:
        return {
            'locations': admin_levels
        }
    # Region is the region of the first geo area
    region = geo_areas[0].admin_level.region
    region_geos = {x['key']: x for x in region.geo_options}

    for area in geo_areas:
        geo_info = region_geos[str(area.id)]
        level = geo_info['admin_level']
        key = f'Admin {level}'
        admin_levels[key] = [*admin_levels.get(key, []), area.title]
        # now add parents as well
        while level - 1:
            level -= 1
            parent_id = geo_info['parent']

            if parent_id is None:
                break

            geo_info = region_geos.get(str(parent_id))
            if not geo_info:
                break

            key = f'Admin {level}'
            admin_levels[key] = [*admin_levels.get(key, []), geo_info['title']]

    return {
        'locations': admin_levels
    }
