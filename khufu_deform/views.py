from khufu_sqlalchemy import dbsession
from khufu_deform._api import model_to_schema
from pyramid.renderers import render_to_response
import deform
from zope.interface import implements, Interface
from sqlalchemy.orm import object_mapper
from pyramid.httpexceptions import HTTPSeeOther

from .utils import ObjectCreatedEvent, ObjectModifiedEvent

_marker = object()


def add_crud_views(c, model_class, container_class):
    '''Setup all possible views for the given model class and
    it's parent class.
    '''

    add_add_form_view(c, model_class, container_class)
    add_edit_form_view(c, model_class)
    add_view_view(c, model_class)
    add_list_view(c, model_class, container_class)


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


def obj_to_dict(obj, schema):
    d = {}
    for col in schema.nodes:
        v = getattr(obj, col.name, _marker)
        if v != _marker:
            d[col.name] = v
    return d


def serialize_pk(obj, schema):
    mapper = object_mapper(obj)
    pk = mapper.primary_key_from_instance(obj)
    return '_'.join([str(x) for x in pk])


def unserialize_pk(s):
    return tuple([int(x) for x in s.split('-')])


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

    def render_form(self, form, obj=None):
        return form.render(obj_to_dict(obj, self.schema), readonly=True)

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
        return form.render(obj_to_dict(obj, self.schema), readonly=True)

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

            m = self.save(request, converted)
            return HTTPSeeOther(location=self.view_url(m, request))

        res = {'form': self.render_form(form, request.context),
               'form_type': self.name,
               'item_label': self.model_label or \
                   self.model_class.__name__.decode('utf-8')}
        res = render_to_response(self.renderer, res, request=request)
        return res

    def get_form(self, request):
        inst = self.schema().bind(db=dbsession(request))
        form = deform.Form(inst, buttons=('add',))
        return form

    def save(self, request, converted):
        m = self.model_class(**converted)
        db = dbsession(request)
        db.add(m)
        db.flush()
        request.registry.notify(ObjectCreatedEvent(m))
        request.session.flash('New %s created' % self.model_label)
        return m

    def view_url(self, m, request):
        return request.relative_url(serialize_pk(m, self.schema))


class ModelEditView(ModelAddView):

    name = 'edit'

    def get_form(self, request):
        schema = self.schema().clone()
        nodes = dict([(x.name, x) for x in schema.children])
        for col in self.model_class.__table__.primary_key:
            if col.name in nodes:
                del nodes[col.name]
        schema.children[:] = nodes.values()

        inst = schema.bind(db=dbsession(request))
        form = deform.Form(inst, buttons=('edit',))
        return form

    def render_form(self, form, obj=None):
        args = []
        if obj is not None:
            args.append(obj_to_dict(obj, self.schema))
        return form.render(*args, readonly=False)

    def save(self, request, converted):
        db = dbsession(request)
        m = request.context
        for k, v in converted.items():
            setattr(m, k, v)
        db.add(m)
        db.flush()
        request.registry.notify(ObjectModifiedEvent(m))
        request.session.flash('%s modified' % m)
        return m

    def view_url(self, m, request):
        return request.relative_url('.')


class ListView(ViewMixin):

    renderer = 'khufu_deform:templates/listing.jinja2'
    model_label = None
    limit = 10

    def __call__(self, request):
        item_label = self.model_label or \
            self.model_class.__name__.decode('utf-8')

        db = dbsession(request)
        if request.method == 'POST':
            q = db.query(self.model_class)
            for x in request.POST.getall('pks'):
                pk = unserialize_pk(x)
                db.delete(q.get(pk))
            db.flush()

        q = db.query(self.model_class)
        start = int(request.params.get('start', 0))
        pager = Pager(q, limit=self.limit, start=start)

        header_items = [x.name.title() for x in self.schema.nodes]

        items = []
        q = db.query(self.model_class)
        for x in pager.items():
            d = obj_to_dict(x, self.schema)
            d['pk'] = serialize_pk(x, self.schema)
            items.append(d)

        res = {'items': items,
               'pager': pager,
               'can_add': True,
               'header_items': header_items,
               'item_label': item_label,
               'fields': self.schema.nodes,
               'request': request}
        return render_to_response(self.renderer, res)


class Pager(object):
    def __init__(self, query, limit=10, start=0):
        self.query = query
        self.limit = limit
        self.start = start

    def items(self):
        q = self.query
        if self.start > 0:
            q = q.offset(self.start)
        return q.limit(self.limit).all()

    def render(self):
        q = self.query
        total = q.count()
        if self.start > 0:
            q = q.offset(self.start)
        q = q.limit(self.limit)

        s = u'%i through %i (%s)' % (self.start, self.start + q.count(), total)
        if self.start > 0:
            start = self.start - self.limit
            if start <= 0:
                start = u'.'
            else:
                start = u'?start=%i' % start
            s = (u'<a class="previous" href="%s">Previous</a>' % start) + s
        if self.start + self.limit < total:
            start = self.start + self.limit
            s += u'<a class="next" href="?start=%i">Next</a>' % start
        return u'<div class="pager">%s</div>' % s
