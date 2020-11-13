WIDGET_ID = 'scaleWidget'

def _get_scale(widget, data, widget_data):
    selected_scale = data.get('value')
    selected_scales = [selected_scale] if selected_scale is not None else []

    scale_units = widget_data.get('scale_units', [])
    scale = next((
        s for s in scale_units
        if s['key'] == selected_scale
    ), None)
    scale = scale or {}
    return {
        # widget_id will be used to alter rendering in report
        'widget_id': getattr(widget, 'widget_id', ''),
        # widget related attributes
        'title': getattr(widget, 'title', ''),
        'label': scale.get('label'),
        'color': scale.get('color'),
    }, selected_scales


def update_attribute(widget, data, widget_data):
    scale, selected_scales = _get_scale(widget, data, widget_data)

    return {
        'filter_data': [{
            'values': selected_scales,
        }],

        'export_data': {
            'data': {
                'version': 1,
                'common': {
                    'widget_id': WIDGET_ID,
                    'widget_key': widget.key,
                },
                'excel': {
                    'value': scale['label'],
                },
                'report': {
                    'title': scale['title'],
                    'label': scale['label'],
                    'color': scale['color'],
                }
            },
        },
    }


def get_comprehensive_data(widgets_meta, widget, data, widget_data):
    scale, selected_scales = _get_scale(widget, data, widget_data)
    scale_units = widget_data.get('scale_units', [])

    if widgets_meta.get(widget.pk) is None:
        widgets_meta[widget.pk] = {
            'min': scale_units[0] if scale_units else None,
            'max': scale_units[len(scale_units) - 1] if scale_units else None,
        }

    return {
        **widgets_meta[widget.pk],
        'scale': scale,
        'label': scale['label'],
        'index': ([
            (i + 1) for i, v in enumerate(scale_units)
            if v['key'] == selected_scales[0]
        ] or [None])[0] if selected_scales else None,
    }
