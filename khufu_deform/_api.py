import colander
import sqlalchemy
from sqlalchemy.sql import func

CAN_VIEW = 'can_view'
CAN_ADD = 'can_add'
CAN_MODIFY = 'can_modify'
CAN_ITERATE = 'can_iterate'


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


class Enum(colander.SchemaType):
    def __init__(self, *options):
        self.options = set(options)

    def serialize(self, node, appstruct):
        if appstruct is colander.null:
            return colander.null

        return appstruct

    def deserialize(self, node, cstruct):
        if not cstruct:
            return colander.null

        if cstruct not in self.options:
            raise NotImplemented('deserializing not yet working')

        return cstruct


class ModelToSchemaMapper(object):

    type_mappings = {
        sqlalchemy.String: colander.String,
        sqlalchemy.Unicode: colander.String,
        sqlalchemy.DateTime: colander.DateTime,
        sqlalchemy.Integer: colander.Integer,
        sqlalchemy.Float: colander.Float,
        sqlalchemy.Boolean: colander.Boolean,
        sqlalchemy.Date: colander.Date,
        sqlalchemy.Time: colander.Time,
        sqlalchemy.Numeric: colander.Float,
        sqlalchemy.Enum: Enum,
        sqlalchemy.TIMESTAMP: colander.DateTime,
        sqlalchemy.SmallInteger: colander.Integer,
        sqlalchemy.Text: colander.String,
        sqlalchemy.BigInteger: colander.Integer,
    }

    def column_to_node(self, model_class, col):
        if isinstance(col.type, sqlalchemy.types.NullType) and \
                len(getattr(col, 'foreign_keys', ())) > 0:
            source_col = tuple(col.foreign_keys)[0].column
            type_factory = self.type_mappings.get(type(source_col.type))
        else:
            type_factory = self.type_mappings.get(type(col.type))

        if type_factory is None:
            raise ValueError('Could not derive colander type '
                             'from: %s (%s)' % (str(col), col.type))

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

    def model_to_schema(self, model_class, excludes=[],
                        omit_primary_key=False):
        nodes = {}
        for col in model_class.__mapper__.columns:
            if col.name in excludes:
                continue
            if col.primary_key and omit_primary_key:
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
