from khufu_deform._internal import (
    model_to_schema,
    view_add_form_config,
    ObjectCreated,
    )


def includeme(config):
    config.add_static_view('deform-static', 'deform:static/')
