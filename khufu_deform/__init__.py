from khufu_deform._api import (
    CAN_ADD,
    CAN_MODIFY,
    CAN_VIEW,
    CAN_ITERATE,
    )

from khufu_deform.views import (
    add_crud_views,
    add_add_form_view,
    add_edit_form_view,
    add_list_view,
    add_view_view,
    )


def includeme(config):
    '''Inclusion helper for Pyramid.
    '''

    config.include('khufu_sqlalchemy')
    config.include('pyramid_jinja2')
    config.add_static_view('deform-static', 'deform:static/')
    config.add_static_view('khufu_deform-static', 'khufu_deform:static/')
    config.add_directive('add_crud_views', add_crud_views)
    config.add_directive('add_add_form_view', add_add_form_view)
    config.add_directive('add_edit_form_view', add_edit_form_view)
    config.add_directive('add_list_view', add_list_view)
    config.add_directive('add_view_view', add_view_view)
