__all__ = ['Aggregator', 'SimpleAggregator', 'Sum', 'Count', 'CountDistinct',
           'Max', 'Min', 'Avg']


class Aggregator(object):

    def process(self, group, val):
        raise NotImplementedError()

    def finish(self, group, default=None):
        raise NotImplementedError()


class SimpleAggregator(Aggregator):

    def __init__(self):
        self._results = {}

    def process(self, group, val):
        pass

    def finish(self, group, default=None):
        return self._results.get(group, default)


class Sum(SimpleAggregator):

    def process(self, group, val):
        tmp = self._results.get(group, 0)
        tmp += val
        self._results[group] = tmp


class Count(SimpleAggregator):

    def process(self, group, val):
        tmp = self._results.get(group, 0)
        tmp += 1
        self._results[group] = tmp


class CountDistinct(SimpleAggregator):

    def process(self, group, val):
        if group not in self._results:
            self._results[group] = set()
        self._results[group].add(val)

    def finish(self, group, default=None):
        if group not in self._results:
            return default
        return len(self._results[group])


class Max(SimpleAggregator):

    def process(self, group, val):
        if group not in self._results:
            self._results[group] = val
        else:
            tmp = self._results[group]
            if val > tmp:
                self._results[group] = val


class Min(SimpleAggregator):

    def process(self, group, val):
        if group not in self._results:
            self._results[group] = val
        else:
            tmp = self._results[group]
            if val < tmp:
                self._results[group] = val


class Avg(Aggregator):

    def __init__(self):
        self.__sum = Sum()
        self.__count = Count()

    def process(self, group, val):
        self.__sum.process(group, val)
        self.__count.process(group, val)

    def finish(self, group, default=None):
        tmp = self.__sum.finish(group, None)
        if tmp is None:
            return default
        else:
            return float(tmp) / self.__count(group)