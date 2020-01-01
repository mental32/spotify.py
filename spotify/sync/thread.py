from asyncio import new_event_loop, run_coroutine_threadsafe, set_event_loop
from threading import Thread, RLock, get_ident
from typing import Any, Coroutine


class EventLoopThread(Thread):
    """A surrogate thread that spins an asyncio event loop."""

    def __init__(self):
        super().__init__(daemon=True)

        self.__lock = RLock()
        self.__loop = loop = new_event_loop()
        loop.__spotify_thread__ = self

    # Properties

    @property
    def loop(self):
        return self.__loop

    # Overloads

    def run(self):
        set_event_loop(self.__loop)
        self.__loop.run_forever()

    # Public API

    def run_coroutine_threadsafe(self, coro: Coroutine) -> Any:
        """Like :func:`asyncio.run_coroutine_threadsafe` but for this specific thread."""

        # If the current thread is the same
        # as the event loop Thread.
        #
        # then we're in the process of making
        # nested calls to await other coroutines
        # and should pass back the coroutine as it should be.
        if get_ident() == self.ident:
            return coro

        # Double lock because I haven't looked
        # into whether this deadlocks under whatever
        # conditions, Best to play it safe.
        with self.__lock:
            future = run_coroutine_threadsafe(coro, self.__loop)

        return future.result()
