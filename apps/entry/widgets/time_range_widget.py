def parse_time(time_string):
    splits = time_string.split(':')
    h = int(splits[0])
    m = int(splits[1])
    return {
        'time_str': '{:02d}:{:02d}'.format(h, m),
        'time_val': h * 60 + m,
    }


def _get_time(widget, data, widget_data):
    value = data.get('value') or {}
    from_value = value.get('from')
    to_value = value.get('to')

    from_time = from_value and parse_time(from_value)
    to_time = to_value and parse_time(to_value)
    return (
        from_time and from_time['time_val'],
        to_time and to_time['time_val'],
    ), (
        from_time and from_time['time_str'],
        to_time and to_time['time_str'],
    )


def update_attribute(widget, data, widget_data):
    (
        from_number,
        to_number,
    ), (
        from_time,
        to_time,
    ) = _get_time(widget, data, widget_data)

    return {
        'filter_data': [{
            'from_number': from_number,
            'to_number': to_number,
        }],

        'export_data': {
            'data': {
                'excel': {
                    'values': [
                        from_time,
                        to_time,
                    ],
                },
            },
        },
    }


def get_comprehensive_data(_, *args):
    (from_time, to_time) = _get_time(*args)[1]
    return {
        'from': from_time,
        'to': to_time,
    }
