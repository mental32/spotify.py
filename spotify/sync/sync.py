import asyncio
import threading
import queue


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

        while self.running:
            if self.out_queue.full():
                self.running = False
                value = self.out_queue.get()
                if isinstance(value, BaseException):
                    raise value
                return value

    def run(self):
        asyncio.set_event_loop(self._loop)

        while True:
            coro = self.in_queue.get()
            try:
                rv = self._loop.run_until_complete(coro)
            except BaseException as error:
                rv = error

            self.out_queue.put(rv)
        self._loop.close()
