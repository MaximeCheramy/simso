import abc


class AbstractExecutionTimeModel(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def init(self):
        pass

    @abc.abstractmethod
    def on_activate(self, _):
        pass

    @abc.abstractmethod
    def update(self):
        pass

    @abc.abstractmethod
    def on_execute(self, _):
        pass

    @abc.abstractmethod
    def on_preempted(self, _):
        pass

    @abc.abstractmethod
    def on_terminated(self, _):
        pass

    @abc.abstractmethod
    def on_abort(self, _):
        pass

    @abc.abstractmethod
    def get_ret(self, _):
        return

    def get_executed(self, job):
        return job.computation_time_cycles
