from khufu_sqlalchemy import dbsession
from khufu_deform._api import model_to_schema
from pyramid.renderers import render_to_response
import deform
from zope.interface import implements, Interface

from .utils import ObjectCreatedEvent, ObjectModifiedEvent

_marker = object()


def add_add_form_view(c, model_class, container_class, name='add',
                      renderer=None):
    '''Setup a new *add form* view for the given *model_class*.
    '''

    view = ModelAddView(c, model_class, renderer=renderer)
    c.add_view(view, name=name, context=container_class)


def add_edit_form_view(c, model_class, name='edit', renderer=None):
    '''Setup a new *edit form* view for the given *model_class*.
    '''

    view = ModelEditView(c, model_class, renderer=renderer)
    c.add_view(view, name=name, context=model_class)


def add_view_view(c, model_class, name='', renderer=None):
    '''Setup a new *view* view for the given *model_class*.
    '''

    view = ModelView(c, model_class, renderer=renderer)
    c.add_view(view, name=name, context=model_class)


def add_list_view(c, model_class, container_class, name='',
                  renderer=None):
    '''Setup a new *list* view for the given *model_class*.
    '''

    view = ListView(c, model_class, renderer=renderer)
    c.add_view(view, context=container_class, name=name)


class ISchemaMappings(Interface):
    pass


class SchemaMappings(object):
    implements(ISchemaMappings)

    def __init__(self):
        self.map = {}


def get_schema_mapping(c, model_class):
    '''Return a colander schema instance for the given model_class,
    ensures this is only done once per model_class.
    '''

    mappings = c.registry.queryUtility(ISchemaMappings)
    if mappings is None:
        mappings = SchemaMappings()
        c.registry.registerUtility(mappings)

    if model_class in mappings.map:
        return mappings.map[model_class]

    schema = model_to_schema(model_class)
    mappings.map[model_class] = schema
    return schema


class ViewMixin(object):
    model_class = None
    schema = None
    renderer = None
    config = None

    def __init__(self, config, model_class, renderer=''):
        self.config = config
        self.model_class = model_class
        self.schema = get_schema_mapping(self.config, self.model_class)
        self.renderer = renderer or self.renderer

    def to_dict(self, obj):
        d = {}
        for col in self.schema.nodes:
            v = getattr(obj, col.name, _marker)
            if v != _marker:
                d[col.name] = v
        return d

    def render_form(self, form, obj=None):
        return form.render(self.to_dict(obj), readonly=True)

    def get_form(self, request):
        inst = self.schema().bind(db=dbsession(request))
        form = deform.Form(inst)
        return form

    def __call__(self, request):
        form = self.get_form(request)
        res = {'form': self.render_form(form, request.context)}
        res = render_to_response(self.renderer, res, request=request)
        return res


class ModelView(ViewMixin):
    model_label = u''
    renderer = 'khufu_deform:templates/generic-view.jinja2'

    def render_form(self, form, obj=None):
        return form.render(self.to_dict(obj), readonly=True)

    def __call__(self, request):
        form = self.get_form(request)
        res = {'form': self.render_form(form, request.context),
               'item': request.context,
               'item_label': self.model_label or \
                   self.model_class.__name__.decode('utf-8')}
        res = render_to_response(self.renderer, res, request=request)
        return res


class ModelAddView(ModelView):

    name = 'add'
    pre_validate = None
    renderer = 'khufu_deform:templates/generic-form.jinja2'

    def render_form(self, form, obj=None):
        return form.render(readonly=False)

    def __call__(self, request):
        form = self.get_form(request)

        if request.method == 'POST':
            form_values = dict(request.POST)
            if self.pre_validate is not None:
                self.pre_validate(form_values)

            try:
                converted = form.validate(form_values.items())
            except deform.ValidationFailure, e:
                return render_to_response(self.renderer,
                                          {'form': e.render()},
                                          request=request)

            self.save(request, converted)

        res = {'form': self.render_form(form, request.context),
               'form_type': self.name,
               'item_label': self.model_label or \
                   self.model_class.__name__.decode('utf-8')}
        res = render_to_response(self.renderer, res, request=request)
        return res

    def save(self, request, converted):
        m = self.model_class(**converted)
        db = dbsession(request)
        db.add(m)
        db.flush()
        request.registry.notify(ObjectCreatedEvent(m))
        request.session.flash('New %s created' % self.model_label)


class ModelEditView(ModelAddView):

    name = 'edit'

    def get_form(self, request):
        inst = self.schema().bind(db=dbsession(request))
        form = deform.Form(inst, buttons=('edit',))
        return form

    def render_form(self, form, obj=None):
        args = []
        if obj is not None:
            args.append(self.to_dict(obj))
        return form.render(*args, readonly=False)

    def save(self, request, converted):
        db = dbsession(request)
        m = db.query(self.model_class).get(converted['id'])
        m.__dict__.update(converted)
        db.add(m)
        db.flush()
        request.registry.notify(ObjectModifiedEvent(m))
        request.session.flash('%s modified' % m)


class ListView(ViewMixin):

    renderer = 'khufu_deform:templates/listing.jinja2'
    model_label = None

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

        res = {'items': q,
               'pager': pager,
               'can_add': can_add,
               'header_items': header_items,
               'item_label': item_label,
               'request': request}
        return render_to_response(self.renderer, res)
