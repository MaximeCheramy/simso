# coding=utf-8

from SimPy.Simulation import Monitor


class Logger(object):
    """
    Simple logger. Every message is logged with its date.
    """
    def __init__(self, sim):
        """
        Args:
            - `sim`: The :class:`model <simso.core.Model.Model>` object.
        """
        self.sim = sim
        self._logs = Monitor(name="Logs", sim=sim)

    def log(self, msg, kernel=False):
        """
        Log the message `msg`.

        Args:
            - `msg`: The message to log.
            - `kernel`: Allows to make a distinction between a message from \
            the core of the simulation or from the scheduler.
        """
        self._logs.observe((msg, kernel))

    @property
    def logs(self):
        """
        The logs, a SimPy Monitor object.
        """
        return self._logs
