import unittest


class MockDBSession(object):
    def query(self, model):
        return self

    def filter(self, *args, **kwargs):
        return self

    def scalar(self):
        return None


class APITests(unittest.TestCase):

    def setUp(self):
        self.db = MockDBSession()

    def test_dbuniquecheck(self):
        from khufu_deform._api import DBUniqueCheck
        check = DBUniqueCheck(self.db, None, None, False)
        check(None, '')


class ModelToSchemaMapperTests(unittest.TestCase):
    def setUp(self):
        import sqlalchemy
        from khufu_deform._api import ModelToSchemaMapper
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base()

        self.mm = ModelToSchemaMapper()

        class Mock(Base):
            __tablename__ = 'foo'
            id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
            col1 = sqlalchemy.Column(sqlalchemy.String(20))
            col2 = sqlalchemy.Column(sqlalchemy.Unicode(20))
            col3 = sqlalchemy.Column(sqlalchemy.DateTime)
            col4 = sqlalchemy.Column(sqlalchemy.Float)
            col5 = sqlalchemy.Column(sqlalchemy.Boolean)
            col6 = sqlalchemy.Column(sqlalchemy.Date)
            col7 = sqlalchemy.Column(sqlalchemy.Time)
            col8 = sqlalchemy.Column(sqlalchemy.Numeric(2))

        self.Mock = Mock

    def test_column_to_node(self):
        for col in self.Mock.__table__.columns:
            node = self.mm.column_to_node(self.Mock, col)
            self.assertTrue(node != None)

    def test_model_to_schema(self):
        self.mm.model_to_schema(self.Mock)
