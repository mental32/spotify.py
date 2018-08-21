import asyncio
import inspect
import functools
import threading
import queue


class SyncMeta:
    def __getattribute__(self, key):
        attr = object.__getattribute__(self, key)

        if inspect.iscoroutinefunction(attr):
            @functools.wraps(attr)
            def decorator(*args, **kwargs):
                return _thread.run_coro(attr(*args, **kwargs))
            setattr(self, key, decorator)
            return decorator
        return attr


class SyncExecution(threading.Thread):
    def __init__(self):
        super().__init__()
        self._loop = asyncio.new_event_loop()
        self.running = False
        self.daemon = True

        self.in_queue = queue.Queue(maxsize=1)
        self.out_queue = queue.Queue(maxsize=1)

    def run_coro(self, coro):
        if self.running:
            return coro

        self.running = True
        self.in_queue.put(coro)

        while True:
            if self.out_queue.full():
                self.running = False
                return self.out_queue.get()

    def run(self):
        asyncio.set_event_loop(self._loop)
        while True:
            coro = self.in_queue.get()
            rv = self._loop.run_until_complete(coro)
            self.out_queue.put(rv)
        self._loop.close()


_thread = SyncExecution()
_thread.start()
