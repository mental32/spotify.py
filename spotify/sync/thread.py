import asyncio
import sys
import threading
import time
import queue
from contextlib import contextmanager, suppress
from typing import Any, Coroutine


class SyncExecution(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)

        self.channel = queue.Queue(maxsize=1)

        self.__lock = threading.RLock()
        self.__loop = loop = asyncio.new_event_loop()

        loop._thread = self

    # Properties

    @property
    def _loop(self):
        return self.__loop

    # threading.Thread

    def run(self):
        asyncio.set_event_loop(self.__loop)

        async def poll():
            channel = self.channel

            while True:
                await asyncio.sleep(0)

                if channel.full():
                    coro, out = channel.get()
                    out.put(self.__loop.create_task(coro))

        self.__loop.create_task(poll())
        self.__loop.run_forever()

    # Public API    

    def run_coro(self, coro: Coroutine) -> Any:
        ident = threading.get_ident()

        # If the current thread is the same
        # as the SyncExecution Thread. then
        # we are making nested calls to await
        # other stuff and should pass back
        # the coroutine as it should be.
        if ident == self.ident:
            return coro

        # Critical work happens here.
        # the purpose of this block is
        # only for scheduling the coroutine
        # to run and getting back the task object.
        with self.__lock:
            output = queue.Queue(maxsize=1)
            self.channel.put((coro, output))
            task = output.get()

        while not task.done():
            # Spinlock that plays nice with other processes on linux systems.
            # See: https://stackoverflow.com/q/7273474/9171481
            time.sleep(0)

        err = task.exception()

        if err:
            raise err
        else:
            return task.result()
