from . import analysis
from .connections import get_connection
from .exceptions import IllegalOperation
from .mapping import Mapping
from .search import Search
from .update_by_query import UpdateByQuery
from .utils import merge


class IndexTemplate(object):
    def __init__(self, name, template, index=None, order=None, **kwargs):
        if index is None:
            self._index = Index(template, **kwargs)
        else:
            if kwargs:
                raise ValueError(
                    "You cannot specify options for Index when"
                    " passing an Index instance."
                )
            self._index = index.clone()
            self._index._name = template
        self._template_name = name
        self.order = order

    def __getattr__(self, attr_name):
        return getattr(self._index, attr_name)

    def to_dict(self):
        d = self._index.to_dict()
        d["index_patterns"] = [self._index._name]
        if self.order is not None:
            d["order"] = self.order
        return d

    def save(self, using=None):

        es = get_connection(using or self._index._using)
        return es.indices.put_template(name=self._template_name, body=self.to_dict())


class Index(object):
    def __init__(self, name, using="default"):
        self._name = name
        self._doc_types = []
        self._using = using
        self._settings = {}
        self._aliases = {}
        self._analysis = {}
        self._mapping = None

    def get_or_create_mapping(self):
        if self._mapping is None:
            self._mapping = Mapping()
        return self._mapping

    def as_template(self, template_name, pattern=None, order=None):
        return IndexTemplate(
            template_name, pattern or self._name, index=self, order=order
        )

    def resolve_nested(self, field_path):
        for doc in self._doc_types:
            nested, field = doc._doc_type.mapping.resolve_nested(field_path)
            if field is not None:
                return nested, field
        if self._mapping:
            return self._mapping.resolve_nested(field_path)
        return (), None

    def resolve_field(self, field_path):
        for doc in self._doc_types:
            field = doc._doc_type.mapping.resolve_field(field_path)
            if field is not None:
                return field
        if self._mapping:
            return self._mapping.resolve_field(field_path)
        return None

    def load_mappings(self, using=None):
        self.get_or_create_mapping().update_from_es(
            self._name, using=using or self._using
        )

    def clone(self, name=None, using=None):
        i = Index(name or self._name, using=using or self._using)
        i._settings = self._settings.copy()
        i._aliases = self._aliases.copy()
        i._analysis = self._analysis.copy()
        i._doc_types = self._doc_types[:]
        if self._mapping is not None:
            i._mapping = self._mapping._clone()
        return i

    def _get_connection(self, using=None):
        if self._name is None:
            raise ValueError("You cannot perform API calls on the default index.")
        return get_connection(using or self._using)

    connection = property(_get_connection)

    def mapping(self, mapping):
        self.get_or_create_mapping().update(mapping)

    def document(self, document):
        self._doc_types.append(document)

        if document._index._name is None:
            document._index = self

        return document

    def settings(self, **kwargs):
        self._settings.update(kwargs)
        return self

    def aliases(self, **kwargs):
        self._aliases.update(kwargs)
        return self

    def analyzer(self, *args, **kwargs):
        analyzer = analysis.analyzer(*args, **kwargs)
        d = analyzer.get_analysis_definition()
        # empty custom analyzer, probably already defined out of our control
        if not d:
            return

        # merge the definition
        merge(self._analysis, d, True)

    def to_dict(self):
        out = {}
        if self._settings:
            out["settings"] = self._settings
        if self._aliases:
            out["aliases"] = self._aliases
        mappings = self._mapping.to_dict() if self._mapping else {}
        analysis = self._mapping._collect_analysis() if self._mapping else {}
        for d in self._doc_types:
            mapping = d._doc_type.mapping
            merge(mappings, mapping.to_dict(), True)
            merge(analysis, mapping._collect_analysis(), True)
        if mappings:
            out["mappings"] = mappings
        if analysis or self._analysis:
            merge(analysis, self._analysis)
            out.setdefault("settings", {})["analysis"] = analysis
        return out

    def search(self, using=None):
        return Search(
            using=using or self._using, index=self._name, doc_type=self._doc_types
        )

    def create(self, using=None, **kwargs):
        return self._get_connection(using).indices.create(
            index=self._name, body=self.to_dict(), **kwargs
        )

    def is_closed(self, using=None):
        state = self._get_connection(using).cluster.state(
            index=self._name, metric="metadata"
        )
        return state["metadata"]["indices"][self._name]["state"] == "close"

    def save(self, using=None):
        if not self.exists(using=using):
            return self.create(using=using)

        body = self.to_dict()
        settings = body.pop("settings", {})
        analysis = settings.pop("analysis", None)
        current_settings = self.get_settings(using=using)[self._name]["settings"][
            "index"
        ]
        if analysis:
            if self.is_closed(using=using):
                settings["analysis"] = analysis
            else:
                existing_analysis = current_settings.get("analysis", {})
                if any(
                    existing_analysis.get(section, {}).get(k, None)
                    != analysis[section][k]
                    for section in analysis
                    for k in analysis[section]
                ):
                    raise IllegalOperation(
                        "You cannot update analysis configuration on an open index, "
                        "you need to close index %s first." % self._name
                    )

        if settings:
            settings = settings.copy()
            for k, v in list(settings.items()):
                if k in current_settings and current_settings[k] == str(v):
                    del settings[k]

            if settings:
                self.put_settings(using=using, body=settings)

        mappings = body.pop("mappings", {})
        if mappings:
            self.put_mapping(using=using, body=mappings)

    def analyze(self, using=None, **kwargs):
        return self._get_connection(using).indices.analyze(index=self._name, **kwargs)

    def refresh(self, using=None, **kwargs):
        return self._get_connection(using).indices.refresh(index=self._name, **kwargs)

    def flush(self, using=None, **kwargs):
        return self._get_connection(using).indices.flush(index=self._name, **kwargs)

    def get(self, using=None, **kwargs):
        return self._get_connection(using).indices.get(index=self._name, **kwargs)

    def open(self, using=None, **kwargs):
        return self._get_connection(using).indices.open(index=self._name, **kwargs)

    def close(self, using=None, **kwargs):
        return self._get_connection(using).indices.close(index=self._name, **kwargs)

    def delete(self, using=None, **kwargs):
        return self._get_connection(using).indices.delete(index=self._name, **kwargs)

    def exists(self, using=None, **kwargs):
        return self._get_connection(using).indices.exists(index=self._name, **kwargs)

    def exists_type(self, using=None, **kwargs):
        return self._get_connection(using).indices.exists_type(
            index=self._name, **kwargs
        )

    def put_mapping(self, using=None, **kwargs):
        return self._get_connection(using).indices.put_mapping(
            index=self._name, **kwargs
        )

    def get_mapping(self, using=None, **kwargs):
        return self._get_connection(using).indices.get_mapping(
            index=self._name, **kwargs
        )

    def get_field_mapping(self, using=None, **kwargs):
        return self._get_connection(using).indices.get_field_mapping(
            index=self._name, **kwargs
        )

    def put_alias(self, using=None, **kwargs):
        return self._get_connection(using).indices.put_alias(index=self._name, **kwargs)

    def exists_alias(self, using=None, **kwargs):
        return self._get_connection(using).indices.exists_alias(
            index=self._name, **kwargs
        )

    def get_alias(self, using=None, **kwargs):
        return self._get_connection(using).indices.get_alias(index=self._name, **kwargs)

    def delete_alias(self, using=None, **kwargs):
        return self._get_connection(using).indices.delete_alias(
            index=self._name, **kwargs
        )

    def get_settings(self, using=None, **kwargs):
        return self._get_connection(using).indices.get_settings(
            index=self._name, **kwargs
        )

    def put_settings(self, using=None, **kwargs):
        return self._get_connection(using).indices.put_settings(
            index=self._name, **kwargs
        )

    def stats(self, using=None, **kwargs):
        return self._get_connection(using).indices.stats(index=self._name, **kwargs)

    def segments(self, using=None, **kwargs):
        return self._get_connection(using).indices.segments(index=self._name, **kwargs)

    def validate_query(self, using=None, **kwargs):
        return self._get_connection(using).indices.validate_query(
            index=self._name, **kwargs
        )

    def clear_cache(self, using=None, **kwargs):
        return self._get_connection(using).indices.clear_cache(
            index=self._name, **kwargs
        )

    def recovery(self, using=None, **kwargs):
        return self._get_connection(using).indices.recovery(index=self._name, **kwargs)

    def upgrade(self, using=None, **kwargs):
        return self._get_connection(using).indices.upgrade(index=self._name, **kwargs)

    def get_upgrade(self, using=None, **kwargs):
        return self._get_connection(using).indices.get_upgrade(
            index=self._name, **kwargs
        )

    def flush_synced(self, using=None, **kwargs):
        return self._get_connection(using).indices.flush_synced(
            index=self._name, **kwargs
        )

    def shard_stores(self, using=None, **kwargs):
        return self._get_connection(using).indices.shard_stores(
            index=self._name, **kwargs
        )

    def forcemerge(self, using=None, **kwargs):
        return self._get_connection(using).indices.forcemerge(
            index=self._name, **kwargs
        )

    def shrink(self, using=None, **kwargs):
        return self._get_connection(using).indices.shrink(index=self._name, **kwargs)
