from __future__ import annotations

import abc
import asyncio
import signal

from loguru import logger


class AbstractAsyncComponent(abc.ABC):
    """Abstract class of asynchronous components."""

    def __init__(self):
        self.initialized = False

    async def _initialize(self) -> None:
        """Do some initialize works."""
        pass

    async def _finalize(self) -> None:
        """Do some cleanup works."""
        pass

    async def initialize(self) -> None:
        """Initialize method wrapper."""
        if self.initialized:
            return
        await self._initialize()
        self.initialized = True

    async def finalize(self) -> None:
        """Finalize method wrapper."""
        if not self.initialized:
            return
        await self._finalize()
        self.initialized = False


class AbstractAsyncRunnable(abc.ABC):
    """Abstract class for which runs tasks in event loop."""

    def __init__(self, *, num_of_tasks: int = 1):
        """Build TaskRunner.

        :param num_of_tasks: Number of tasks to run.
        :type num_of_tasks: int
        """
        self.started = False
        self.should_exit = False
        self.num_of_tasks = num_of_tasks

    @abc.abstractmethod
    async def _startup(self):
        """Do some initialize works."""
        raise NotImplementedError()

    @abc.abstractmethod
    async def _main_task(self, *, number: int):
        """The main task to run.

        :param number: Serial number.
        :type number: int
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def _shutdown(self):
        """Do some cleanup works."""
        raise NotImplementedError()

    async def _run(self) -> None:
        """Run tasks in event loop."""

        loop = asyncio.get_event_loop()
        loop.add_signal_handler(
            signal.SIGINT,
            lambda: asyncio.create_task(
                self.handle_exit_signal(sig_name='SIGINT')
            ),
        )
        loop.add_signal_handler(
            signal.SIGTERM,
            lambda: asyncio.create_task(
                self.handle_exit_signal(sig_name='SIGTERM')
            ),
        )

        await self.startup()
        await asyncio.gather(
            *[self.main_task(number=x) for x in range(self.num_of_tasks)]
        )
        await self.shutdown()

    def run(self) -> None:
        """The entrypoint to run in event loop."""
        asyncio.run(self._run())

    async def handle_exit_signal(self, *, sig_name: str) -> None:
        """Callback function for handing SIGINT and SIGTERM signal.

        :param sig_name: Signal type.
        :type sig_name: str
        """
        logger.info(f'The `{sig_name}` signal is received.')
        self.should_exit = True

    async def startup(self) -> None:
        """Startup method wrapper."""
        if self.should_exit:
            return
        logger.info(
            f'Preparing to start the main loop of `{type(self).__name__}`.'
        )
        await self._startup()
        self.started = True
        logger.info(f'The main loop of `{type(self).__name__}` started.')

    async def main_task(self, *, number: int) -> None:
        """Main task method wrapper.
        :param number: Serial number.
        :type number: int
        :return:
        :rtype:
        """
        logger.info(f'Task{number} starts to process request message.')
        while not self.should_exit:
            await self._main_task(number=number)
        logger.info(f'Task{number} exit.')

    async def shutdown(self) -> None:
        """Shutdown method wrapper."""
        if not self.should_exit:
            return
        if not self.started:
            return

        logger.info(
            f'Preparing to exit the main loop of `{type(self).__name__}`.'
        )
        await self._shutdown()
        self.started = False
        logger.info(f'The main loop of `{type(self).__name__}` exited.')
