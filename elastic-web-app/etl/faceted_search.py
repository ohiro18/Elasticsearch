
from datetime import datetime, timedelta

from six import iteritems, itervalues

from .aggs import A
from .query import MatchAll, Nested, Range, Terms
from .response import Response
from .search import Search
from .utils import AttrDict

__all__ = [
    "FacetedSearch",
    "HistogramFacet",
    "TermsFacet",
    "DateHistogramFacet",
    "RangeFacet",
    "NestedFacet",
]


class Facet(object):

    agg_type = None

    def __init__(self, metric=None, metric_sort="desc", **kwargs):
        self.filter_values = ()
        self._params = kwargs
        self._metric = metric
        if metric and metric_sort:
            self._params["order"] = {"metric": metric_sort}

    def get_aggregation(self):
        agg = A(self.agg_type, **self._params)
        if self._metric:
            agg.metric("metric", self._metric)
        return agg

    def add_filter(self, filter_values):
        if not filter_values:
            return

        f = self.get_value_filter(filter_values[0])
        for v in filter_values[1:]:
            f |= self.get_value_filter(v)
        return f

    def get_value_filter(self, filter_value):
        pass

    def is_filtered(self, key, filter_values):
        return key in filter_values

    def get_value(self, bucket):
        return bucket["key"]

    def get_metric(self, bucket):
        if self._metric:
            return bucket["metric"]["value"]
        return bucket["doc_count"]

    def get_values(self, data, filter_values):
        out = []
        for bucket in data.buckets:
            key = self.get_value(bucket)
            out.append(
                (key, self.get_metric(bucket), self.is_filtered(key, filter_values))
            )
        return out


class TermsFacet(Facet):
    agg_type = "terms"

    def add_filter(self, filter_values):
        if filter_values:
            return Terms(
                _expand__to_dot=False, **{self._params["field"]: filter_values}
            )


class RangeFacet(Facet):
    agg_type = "range"

    def _range_to_dict(self, range):
        key, range = range
        out = {"key": key}
        if range[0] is not None:
            out["from"] = range[0]
        if range[1] is not None:
            out["to"] = range[1]
        return out

    def __init__(self, ranges, **kwargs):
        super(RangeFacet, self).__init__(**kwargs)
        self._params["ranges"] = list(map(self._range_to_dict, ranges))
        self._params["keyed"] = False
        self._ranges = dict(ranges)

    def get_value_filter(self, filter_value):
        f, t = self._ranges[filter_value]
        limits = {}
        if f is not None:
            limits["gte"] = f
        if t is not None:
            limits["lt"] = t

        return Range(_expand__to_dot=False, **{self._params["field"]: limits})


class HistogramFacet(Facet):
    agg_type = "histogram"

    def get_value_filter(self, filter_value):
        return Range(
            _expand__to_dot=False,
            **{
                self._params["field"]: {
                    "gte": filter_value,
                    "lt": filter_value + self._params["interval"],
                }
            }
        )


def _date_interval_month(d):
    return (d + timedelta(days=32)).replace(day=1)


def _date_interval_week(d):
    return d + timedelta(days=7)


def _date_interval_day(d):
    return d + timedelta(days=1)


def _date_interval_hour(d):
    return d + timedelta(hours=1)


class DateHistogramFacet(Facet):
    agg_type = "date_histogram"

    DATE_INTERVALS = {
        "month": _date_interval_month,
        "1M": _date_interval_month,
        "week": _date_interval_week,
        "1w": _date_interval_week,
        "day": _date_interval_day,
        "1d": _date_interval_day,
        "hour": _date_interval_hour,
        "1h": _date_interval_hour,
    }

    def __init__(self, **kwargs):
        kwargs.setdefault("min_doc_count", 0)
        super(DateHistogramFacet, self).__init__(**kwargs)

    def get_value(self, bucket):
        if not isinstance(bucket["key"], datetime):
            if bucket["key"] is None:
                bucket["key"] = 0
            return datetime.utcfromtimestamp(int(bucket["key"]) / 1000.0)
        else:
            return bucket["key"]

    def get_value_filter(self, filter_value):
        for interval_type in ("calendar_interval", "fixed_interval"):
            if interval_type in self._params:
                break
        else:
            interval_type = "interval"

        return Range(
            _expand__to_dot=False,
            **{
                self._params["field"]: {
                    "gte": filter_value,
                    "lt": self.DATE_INTERVALS[self._params[interval_type]](
                        filter_value
                    ),
                }
            }
        )


class NestedFacet(Facet):
    agg_type = "nested"

    def __init__(self, path, nested_facet):
        self._path = path
        self._inner = nested_facet
        super(NestedFacet, self).__init__(
            path=path, aggs={"inner": nested_facet.get_aggregation()}
        )

    def get_values(self, data, filter_values):
        return self._inner.get_values(data.inner, filter_values)

    def add_filter(self, filter_values):
        inner_q = self._inner.add_filter(filter_values)
        if inner_q:
            return Nested(path=self._path, query=inner_q)


class FacetedResponse(Response):
    @property
    def query_string(self):
        return self._faceted_search._query

    @property
    def facets(self):
        if not hasattr(self, "_facets"):
            super(AttrDict, self).__setattr__("_facets", AttrDict({}))
            for name, facet in iteritems(self._faceted_search.facets):
                self._facets[name] = facet.get_values(
                    getattr(getattr(self.aggregations, "_filter_" + name), name),
                    self._faceted_search.filter_values.get(name, ()),
                )
        return self._facets


class FacetedSearch(object):
    index = None
    doc_types = None
    fields = None
    facets = {}
    using = "default"

    def __init__(self, query=None, filters={}, sort=()):
        self._query = query
        self._filters = {}
        self._sort = sort
        self.filter_values = {}
        for name, value in iteritems(filters):
            self.add_filter(name, value)

        self._s = self.build_search()

    def count(self):
        return self._s.count()

    def __getitem__(self, k):
        self._s = self._s[k]
        return self

    def __iter__(self):
        return iter(self._s)

    def add_filter(self, name, filter_values):
        if not isinstance(filter_values, (tuple, list)):
            if filter_values is None:
                return
            filter_values = [
                filter_values,
            ]

        self.filter_values[name] = filter_values

        f = self.facets[name].add_filter(filter_values)
        if f is None:
            return

        self._filters[name] = f

    def search(self):
        s = Search(doc_type=self.doc_types, index=self.index, using=self.using)
        return s.response_class(FacetedResponse)

    def query(self, search, query):
        if query:
            if self.fields:
                return search.query("multi_match", fields=self.fields, query=query)
            else:
                return search.query("multi_match", query=query)
        return search

    def aggregate(self, search):
        for f, facet in iteritems(self.facets):
            agg = facet.get_aggregation()
            agg_filter = MatchAll()
            for field, filter in iteritems(self._filters):
                if f == field:
                    continue
                agg_filter &= filter
            search.aggs.bucket("_filter_" + f, "filter", filter=agg_filter).bucket(
                f, agg
            )

    def filter(self, search):
        if not self._filters:
            return search

        post_filter = MatchAll()
        for f in itervalues(self._filters):
            post_filter &= f
        return search.post_filter(post_filter)

    def highlight(self, search):
        return search.highlight(
            *(f if "^" not in f else f.split("^", 1)[0] for f in self.fields)
        )

    def sort(self, search):
        if self._sort:
            search = search.sort(*self._sort)
        return search

    def build_search(self):
        s = self.search()
        s = self.query(s, self._query)
        s = self.filter(s)
        if self.fields:
            s = self.highlight(s)
        s = self.sort(s)
        self.aggregate(s)
        return s

    def execute(self):
        r = self._s.execute()
        r._faceted_search = self
        return r
        
        
