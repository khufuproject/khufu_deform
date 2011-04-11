import colander
import deform
from sqlalchemy.sql import func
import sqlalchemy
from pyramid.view import view_config
from khufu_sqlalchemy import dbsession
from pyramid.httpexceptions import HTTPTemporaryRedirect


class DBUniqueCheck(object):
    def __init__(self, db, model_class, field, case_sensitive=True):
        self.db = db
        self.model_class = model_class
        self.field = field
        self.case_sensitive = case_sensitive

    def __call__(self, node, value):
        query = self.db.query(self.model_class)
        f = self.field
        v = value
        if not self.case_sensitive:
            f = func.lower(self.field)
            v = value.lower()
        if query.filter(f == v).scalar() is not None:
            s = (u'A %s already exists with that %s'
                 % (self.model_class.__name__.lower(), node.name))
            raise colander.Invalid(node, s)


class DeferredDBCheck(colander.deferred):
    def __init__(self, valid_callable, **kwargs):
        self.valid_callable = valid_callable
        self.kwargs = kwargs

    def __call__(self, node, kwargs):
        db = kwargs['db']
        return self.valid_callable(db, **self.kwargs)


class DeferredAll(colander.deferred):
    def __init__(self, *validators):
        self.validators = list(validators)

    def __call__(self, node, kwargs):
        full = []
        for x in self.validators:
            if isinstance(x, colander.deferred):
                full.append(x(node, kwargs))
            else:
                full.append(x)
        return colander.All(*full)


class ModelToSchemaMapper(object):

    type_mappings = {
        sqlalchemy.String: colander.String,
        sqlalchemy.Unicode: colander.String,
        sqlalchemy.DateTime: colander.DateTime,
        sqlalchemy.Integer: colander.Integer,
    }

    def column_to_node(self, model_class, col):
        if isinstance(col.type, sqlalchemy.types.NullType) and \
                len(getattr(col, 'foreign_keys', ())) > 0:
            source_col = col.foreign_keys[0].column
            type_factory = self.type_mappings.get(type(source_col.type))
        else:
            type_factory = self.type_mappings.get(type(col.type))

        if type_factory is None:
            raise ValueError('Could not derive colander type '
                             'from: %s' % str(col))

        kwargs = {'typ': type_factory()}
        if col.nullable:
            kwargs['missing'] = colander.null

        if hasattr(col.type, 'length'):
            self._add_validator(kwargs, colander.Length(max=col.type.length))

        if col.primary_key:
            self._add_validator(
                kwargs, DeferredDBCheck(DBUniqueCheck,
                                        model_class=model_class,
                                        field=col))

        return colander.SchemaNode(**kwargs)

    def model_to_schema(self, model_class, excludes=[]):
        nodes = {}
        for col in model_class.__mapper__.columns:
            if col.name in excludes:
                continue
            node = self.column_to_node(model_class, col)
            nodes[col.name] = node

        return type(model_class.__name__ + 'Schema',
                    (colander.MappingSchema,),
                    nodes)

    def _add_validator(self, info, validator):
        group = info.get('validator')
        if group is None:
            info['validator'] = group = DeferredAll()
        group.validators.append(validator)


model_to_schema = ModelToSchemaMapper().model_to_schema


class AddFormView(object):
    def __init__(self, model, name='add',
                 renderer='', pre_validate=None,
                 model_label=u'',
                 validator=None,
                 excludes=[]):
        self.model = model
        self.name = name
        self.model_label = model_label
        self.renderer = renderer or \
            'khufu_deform:templates/generic-form.jinja2'
        self.pre_validate = pre_validate
        self.schema = model_to_schema(self.model, excludes)
        self.validator = validator

    def __call__(self, request):
        kwargs = {}
        if self.validator is not None:
            kwargs['validator'] = self.validator
        inst = self.schema(**kwargs)
        form = deform.Form(inst.bind(db=dbsession(request)),
                           buttons=('add',))
        if 'add' in request.POST:
            form_values = dict(request.POST)
            if self.pre_validate is not None:
                self.pre_validate(form_values)

            try:
                converted = form.validate(form_values.items())
            except deform.ValidationFailure, e:
                return {'form': e.render()}

            m = self.model(**converted)
            db = dbsession(request)
            db.add(m)
            db.flush()
            request.registry.notify(ObjectCreated(m))
            request.session.flash('New %s created' % self.model_label)

        return {'form': form.render(),
                'item_label': self.model_label or \
                    self.model.__name__.decode('utf-8')}


class ObjectCreated(object):
    def __init__(self, obj):
        self.obj = obj



class view_add_form_config(object):
    '''A decorator to identify a function as being pre-form-processing
    validator for a new form view.
    '''

    def __init__(self, model, context,
                 renderer='', name='add',
                 model_label=u'',
                 validator=None,
                 permission=None,
                 excludes=[]):
        self.renderer = renderer or \
            'khufu_deform:templates/generic-form.jinja2'

        v = view_config(context=context,
                        name=name,
                        renderer=self.renderer,
                        permission=permission)
        self.view = v(AddFormView(model,
                                  model_label=model_label,
                                  name=name,
                                  excludes=excludes,
                                  validator=validator))

    def __call__(self, f):
        self.view.pre_validate = f
        return self.view
