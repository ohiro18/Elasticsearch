
        try:
            while True:  # At one point there will be a StopIteration
                if keyval1 == keyval2:
                    # Output rows
                    for part in rows2:
                        resrow = row1.copy()
                        resrow.update(part)
                        yield resrow
                    row1 = next(iter1)
                    keyval1 = row1[self.__key1]
                elif keyval1 < keyval2:
                    row1 = next(iter1)
                    keyval1 = row1[self.__key1]
                else:  # k1 > k2
                    rows2 = self.__getnextrows(iter2)
                    keyval2 = rows2[0][self.__key2]
        except StopIteration:
            return # Needed in Python 3.7+ due to PEP 479

    def __getnextrows(self, iterval):
        res = []
        keyval = None
        if self.__next is not None:
            res.append(self.__next)
            keyval = self.__next[self.__key2]
            self.__next = None
        while True:
            try:
                row = next(iterval)
            except StopIteration:
                if res:
                    return res
                else:
                    raise
            if keyval is None:
                keyval = row[self.__key2]  # for the first row in this round
            if row[self.__key2] == keyval:
                res.append(row)
            else:
                self.__next = row
                return res


class MappingSource(object):
    """A class for iterating a source and applying a function to each column."""

    def __init__(self, source, callables):
        """Arguments:
           - source: A data source
           - callables: A dict mapping from attribute names to functions to
             apply to these names, e.g. type casting {'id':int, 'salary':float}
        """
        if not type(callables) == dict:
            raise TypeError("The callables argument must be a dict")
        for v in callables.values():
            if not callable(v):
                raise TypeError("The values in callables must be callable")

        self._source = source
        self._callables = callables

    def __iter__(self):
        for row in self._source:
            for (att, func) in self._callables.items():
                row[att] = func(row[att])
                yield row


class TransformingSource(object):

    """A source that applies functions to the rows from another source"""

    def __init__(self, source, *transformations):
        """Arguments:
            
        - source: a data source
        - *transformations: the transformations to apply. Must be callables
          of the form func(row) where row is a dict. Will be applied in the
          given order.
        """
        self.__source = source
        self.__transformations = transformations

    def __iter__(self):
        for row in self.__source:
            for func in self.__transformations:
                func(row)
            yield row


class CrossTabbingSource(object):

    """A source that produces a crosstab from another source"""

    def __init__(self, source, rowvaluesatt, colvaluesatt, values,
                 aggregator=None, nonevalue=0, sortrows=False):
        """Arguments:
            
        - source: the data source to pull data from
        - rowvaluesatt: the name of the attribute that holds the values that
          appear as rows in the result
        - colvaluesatt: the name of the attribute that holds the values that
          appear as columns in the result
        - values: the name of the attribute that holds the values to aggregate
        - aggregator: the aggregator to use (see pygrametl.aggregators). If not
          given, pygrametl.aggregators.Sum is used to sum the values
        - nonevalue: the value to return when there is no data to aggregate.
          Default: 0
        - sortrows: A boolean deciding if the rows should be sorted.
          Default: False
        """
        self.__source = source
        self.__rowvaluesatt = rowvaluesatt
        self.__colvaluesatt = colvaluesatt
        self.__values = values
        if aggregator is None:
            from pygrametl.aggregators import Sum
            self.__aggregator = Sum()
        else:
            self.__aggregator = aggregator
        self.__nonevalue = nonevalue
        self.__sortrows = sortrows
        self.__allcolumns = set()
        self.__allrows = set()

    def __iter__(self):
        for data in self.__source:  # first we iterate over all source data ...
            row = data[self.__rowvaluesatt]
            col = data[self.__colvaluesatt]
            self.__allrows.add(row)
            self.__allcolumns.add(col)
            self.__aggregator.process((row, col), data[self.__values])

        # ... and then we build result rows
        for row in (self.__sortrows and sorted(self.__allrows) or
                    self.__allrows):
            res = {self.__rowvaluesatt: row}
            for col in self.__allcolumns:
                res[col] = \
                    self.__aggregator.finish((row, col), self.__nonevalue)
            yield res


class FilteringSource(object):

    """A source that applies a filter to another source"""

    def __init__(self, source, filter=bool):
        """Arguments:
            
           - source: the source to filter
           - filter: a callable f(row). If the result is a True value,
             the row is passed on. If not, the row is discarded.
             Default: bool, i.e., Python's standard boolean conversion which
             removes empty rows.
        """
        self.__source = source
        self.__filter = filter

    def __iter__(self):
        for row in self.__source:
            if self.__filter(row):
                yield row


class UnionSource(object):

    """A source to union other sources (possibly with different types of rows).
    All rows are read from the 1st source before rows are read from the 2nd
    source and so on (to interleave the rows, use a RoundRobinSource)
    """

    def __init__(self, *sources):
        """Arguments:
            
           - *sources: The sources to union in the order they should be used.
        """
        self.__sources = sources

    def __iter__(self):
        for src in self.__sources:
            for row in src:
                yield row


class RoundRobinSource(object):

    """A source that reads sets of rows from sources in round robin-fashion"""

    def __init__(self, sources, batchsize=500):
        """Arguments:
            
           - sources: a sequence of data sources
           - batchsize: the amount of rows to read from a data source before
             going to the next data source. Must be positive (to empty a source
             before going to the next, use UnionSource)
        """
        self.__sources = [iter(src) for src in sources]
        self.__sources.reverse()  # we iterate it from the back in __iter__
        if not batchsize > 0:
            raise ValueError("batchsize must be positive")
        self.__batchsize = batchsize

    def __iter__(self):
        while self.__sources:
            # iterate from back
            for i in range(len(self.__sources) - 1, -1, -1):
                cursrc = self.__sources[i]
                # now return up to __batchsize from cursrc
                try:
                    for _ in range(self.__batchsize):
                        yield next(cursrc)
                except StopIteration:
                    # we're done with this source and can delete it since
                    # we iterate the list as we do
                    del self.__sources[i]
        return


class DynamicForEachSource(object):

    """A source that for each given argument creates a new source that
    will be iterated by this source.
    For example, useful for directories where a CSVSource should be created
    for each file.
    The user must provide a function that when called with a single argument,
    returns a new source to iterate. A DynamicForEachSource instance can be
    given to several ProcessSource instances.
    """

    def __init__(self, seq, callee):
        """Arguments:
            
           - seq: a sequence with the elements for each of which a unique
             source must be created. the elements are given (one by one) to
             callee.
           - callee: a function f(e) that must accept elements as those in the
             seq argument. the function should return a source which then will
             be iterated by this source. the function is called once for every
             element in seq.
        """
        self.__queue = Queue()  # a multiprocessing.Queue
        if not callable(callee):
            raise TypeError('callee must be callable')
        self.__callee = callee
        for e in seq:
            # put them in a safe queue such that this object can be used from
            # different fork'ed processes
            self.__queue.put(e)

    def __iter__(self):
        while True:
            try:
                arg = self.__queue.get(False)
                src = self.__callee(arg)
                for row in src:
                    yield row
            except Empty:
                return