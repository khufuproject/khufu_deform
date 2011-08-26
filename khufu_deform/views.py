from khufu_sqlalchemy import dbsession
from khufu_deform._api import model_to_schema
from pyramid.renderers import render_to_response
import deform

from .utils import ObjectCreated


class AddView(object):

    model_class = None
    model_label = u''

    def __init__(self, model_class, renderer=''):
        self.model_class = model_class
        self.schema = model_to_schema(self.model_class)
        self.renderer = renderer or \
            'khufu_deform:templates/generic-form.jinja2'

    def __call__(self, request):
        kwargs = {}
        db = dbsession(request)
        inst = self.schema(**kwargs).bind(db=db)
        form = deform.Form(inst, buttons=('add',))
        if 'add' in request.POST:
            form_values = dict(request.POST)
            if self.pre_validate is not None:
                self.pre_validate(form_values)

            try:
                converted = form.validate(form_values.items())
            except deform.ValidationFailure, e:
                return {'form': e.render()}

            m = self.model_class(**converted)
            db = dbsession(request)
            db.add(m)
            db.flush()
            request.registry.notify(ObjectCreated(m))
            request.session.flash('New %s created' % self.model_label)

        res = {'form': form.render(),
               'item_label': self.model_label or \
                   self.model_class.__name__.decode('utf-8')}
        res = render_to_response(self.renderer, res, request=request)
        return res


def add_add_form_view(c, model_class, container_class, name='add'):
    view = AddView(model_class)
    c.add_view(view, name=name, context=container_class)


def add_edit_form_view(c, model_class, name='edit'):
    pass


def add_view_view(c, model_class, name=''):
    pass


class ListView(object):
    def __init__(self, model_class, container_class, model_label=None):
        self.model_class = model_class
        self.container_class = container_class
        self.model_label = model_label
        self.schema = model_to_schema(self.model_class)

    def __call__(self, request):
        item_label = self.model_label or \
            self.model_class.__name__.decode('utf-8')

        limit = 10
        firstcol = self.model_class.__mapper__.columns.keys()[0]
        firstcol = self.model_class.__mapper__.columns[firstcol]
        q = dbsession(request).query(firstcol)
        total = q.count()

        q = dbsession(request).query(*self.model_class.__mapper__.columns)
        q = q.limit(limit)
        pager = u''
        if q.count() < total:
            pager = 'displaying %i of %i items' % (q.count(), total)

        header_items = [x.name.title() for x in self.schema.nodes]

        can_add = True

        return {'items': q,
                'pager': pager,
                'can_add': can_add,
                'header_items': header_items,
                'item_label': item_label}


def add_list_view(c, model_class, container_class, name=''):
    view = ListView(model_class, container_class)
    c.add_view(view, context=container_class, name=name,
               renderer='khufu_deform:templates/listing.jinja2')
