from elasticsearch import Elasticsearch
from six import string_types

from .serializer import serializer


class Connections(object):

    def __init__(self):
        self._kwargs = {}
        self._conns = {}

    def configure(self, **kwargs):
        for k in list(self._conns):
            # try and preserve existing client to keep the persistent connections alive
            if k in self._kwargs and kwargs.get(k, None) == self._kwargs[k]:
                continue
            del self._conns[k]
        self._kwargs = kwargs

    def add_connection(self, alias, conn):
        self._conns[alias] = conn

    def remove_connection(self, alias):
        errors = 0
        for d in (self._conns, self._kwargs):
            try:
                del d[alias]
            except KeyError:
                errors += 1

        if errors == 2:
            raise KeyError("There is no connection with alias %r." % alias)

    def create_connection(self, alias="default", **kwargs):
        kwargs.setdefault("serializer", serializer)
        conn = self._conns[alias] = Elasticsearch(**kwargs)
        return conn

    def get_connection(self, alias="default"):
        if not isinstance(alias, string_types):
            return alias

        try:
            return self._conns[alias]
        except KeyError:
            pass

        try:
            return self.create_connection(alias, **self._kwargs[alias])
        except KeyError:
            raise KeyError("There is no connection with alias %r." % alias)


connections = Connections()
configure = connections.configure
add_connection = connections.add_connection
remove_connection = connections.remove_connection
create_connection = connections.create_connection
get_connection = connections.get_connection
