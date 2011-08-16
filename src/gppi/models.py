# -*- coding: utf-8 -*-

import uuid

from django.db.models import *
from django.db.models import Model as Model_django

from django.db.models import CharField

class UUIDField (CharField, ) :
    """ UUIDField

    By default uses UUID version 1 (generate from host ID, sequence number and
    current time)

    The field support all uuid versions which are natively supported by the
    uuid python module.  For more information see :
    http://docs.python.org/lib/module-uuid.html

    """

    def __init__(self, verbose_name=None, name=None, auto=False, version=1, node=None,
            clock_seq=None, namespace=None, **kwargs) :
        kwargs['max_length'] = 32
        if auto :
            kwargs['blank'] = True
            kwargs.setdefault('editable', False)
        self.auto = auto
        self.version = version
        if version == 1 :
            self.node, self.clock_seq = node, clock_seq
        elif version == 3 or version == 5 :
            self.namespace, self.name = namespace, name
        CharField.__init__(self, verbose_name, name, **kwargs)

    def get_internal_type(self) :
        return CharField.__name__

    def contribute_to_class(self, cls, name) :
        if self.primary_key :
            _MM = "A model can't have more than one AutoField: %s %s %s; have %s"
            assert not cls._meta.has_auto_field, _MM % (
                    self, cls, name, cls._meta.auto_field, )
            super(UUIDField, self).contribute_to_class(cls, name)
            cls._meta.has_auto_field = True
            cls._meta.auto_field = self
        else :
            super(UUIDField, self).contribute_to_class(cls, name)

    def create_uuid(self) :
        if not self.version or self.version == 4 :
            return uuid.uuid4()
        elif self.version == 1 :
            return uuid.uuid1(self.node, self.clock_seq)
        elif self.version == 2 :
            raise UUIDVersionError("UUID version 2 is not supported.")
        elif self.version == 3 :
            return uuid.uuid3(self.namespace, self.name)
        elif self.version == 5 :
            return uuid.uuid5(self.namespace, self.name)
        else :
            raise UUIDVersionError("UUID version %s is not valid." % self.version)

    def pre_save(self, model_instance, add) :
        if self.auto and add :
            value = self.create_uuid().hex
            setattr(model_instance, self.attname, value)
            return value
        else :
            value = super(UUIDField, self).pre_save(model_instance, add)
            if self.auto and not value :
                value = self.create_uuid().hex
                setattr(model_instance, self.attname, value)
        return value


class Model (Model_django, ) :
    class Meta :
        abstract = True

    key = UUIDField(auto=True, primary_key=True, )





if __name__ == "__main__"  :
    import doctest
    doctest.testmod()




