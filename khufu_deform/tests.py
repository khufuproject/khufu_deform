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
