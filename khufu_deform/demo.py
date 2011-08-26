import os
from paste.httpserver import serve
from khufu_sqlalchemy import dbsession
from sqlalchemy import Column, Integer, Unicode, create_engine
from sqlalchemy.ext.declarative import declarative_base
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.session import UnencryptedCookieSessionFactoryConfig

Base = declarative_base()

INITIAL_DATA = [
    (1, 'this is a random note'),
    (2, 'bah i hate writing notes'),
    (3, 'foo bar me so rae'),
    (4, 'foo bar me so rae'),
    (5, 'foo bar me so rae'),
    (6, 'foo bar me so rae'),
    (7, 'foo bar me so rae'),
    (8, 'foo bar me so rae'),
    (9, 'foo bar me so rae'),
    (10, 'foo bar me so rae'),
    (11, 'foo bar me so rae'),
    (12, 'foo bar me so rae'),
    (13, 'foo bar me so rae'),
    (14, 'foo bar me so rae'),
    (15, 'foo bar me so rae'),
    (16, 'foo bar me so rae'),
    (17, 'foo bar me so rae'),
    (18, 'foo bar me so rae'),
    (19, 'foo bar me so rae'),
    (20, 'foo bar me so rae'),
    (21, 'foo bar me so rae'),
]


class Root(dict):
    __name__ = None
    __parent__ = None

    def __init__(self, request):
        self.request = request
        self.db = dbsession(request)
        self['notes'] = NoteContainer()


def root(request):
    return Response(body='<a href="%s">Notes</a>'
                    % request.resource_url(request.context, 'notes'))


class NoteContainer(object):
    pass


class Note(Base):
    __tablename__ = 'khufu_deform_note'

    id = Column(Integer, primary_key=True)
    text = Column(Unicode(200), nullable=True)


def app(global_conf, **settings):
    dbfile = '/tmp/khufu_deform.db'
    if not os.path.exists(dbfile):
        engine = create_engine('sqlite:///' + dbfile)
        Base.metadata.create_all(bind=engine)
        for item in INITIAL_DATA:
            engine.execute("insert into khufu_deform_note values %r" % (item, ))
    else:
        engine = create_engine('sqlite:///' + dbfile)

    settings.setdefault('khufu.dbengine', engine)
    config = Configurator(
        settings=settings,
        root_factory=Root,
        session_factory=UnencryptedCookieSessionFactoryConfig('itsaseekreet'))
    config.include('khufu_deform')
    config.add_add_form_view(model_class=Note,
                             container_class=NoteContainer)
    config.add_list_view(model_class=Note,
                         container_class=NoteContainer)
    return config.make_wsgi_app()


if __name__ == '__main__':
    print "Serving on port 8000..."
    serve(app({}), host='0.0.0.0')
