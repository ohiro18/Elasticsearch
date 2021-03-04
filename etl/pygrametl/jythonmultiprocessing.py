from threading import Thread

from pygrametl.jythonsupport import Value


# Needed for both pip2 and pip3 to be supported
try:
    from Queue import Queue
except ImportError:
    from queue import Queue

# NOTE: This module is made for Jython.

__all__ = ['JoinableQueue', 'Process', 'Queue', 'Value']


class Process(Thread):
    pid = '<n/a>'
    daemon = property(Thread.isDaemon, Thread.setDaemon)
    name = property(Thread.getName, Thread.setName)


class JoinableQueue(Queue):

    def close(self):
        pass