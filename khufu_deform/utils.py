class ObjectEvent(object):
    def __init__(self, obj):
        self.obj = obj


class ObjectCreatedEvent(ObjectEvent):
    pass


class ObjectModifiedEvent(ObjectEvent):
    pass
