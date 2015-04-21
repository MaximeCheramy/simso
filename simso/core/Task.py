# coding=utf-8

from collections import deque
from SimPy.Simulation import Process, Monitor, hold, passivate
from simso.core.Job import Job
from simso.core.Timer import Timer
from .CSDP import CSDP

import os
import os.path


class TaskInfo(object):
    """
    TaskInfo is mainly a container class grouping the data that characterize
    a Task. A list of TaskInfo objects are passed to the Model so that
    :class:`Task` instances can be created.
    """

    def __init__(self, name, identifier, task_type, abort_on_miss, period,
                 activation_date, n_instr, mix, stack_file, wcet, acet,
                 et_stddev, deadline, base_cpi, followed_by,
                 list_activation_dates, preemption_cost, data):
        """
        :type name: str
        :type identifier: int
        :type task_type: str
        :type abort_on_miss: bool
        :type period: float
        :type activation_date: float
        :type n_instr: int
        :type mix: float
        :type stack_file: str
        :type wcet: float
        :type acet: float
        :type et_stddev: float
        :type deadline: float
        :type base_cpi: float
        :type followed_by: int
        :type list_activation_dates: list
        :type preemption_cost: int
        :type data: dict
        """
        self.name = name
        self.identifier = identifier
        self.task_type = task_type
        self.period = period
        self.activation_date = activation_date
        self.n_instr = n_instr
        self.mix = mix
        self.wcet = wcet
        self.acet = acet
        self.et_stddev = et_stddev
        self.base_cpi = base_cpi
        self._stack = None
        self._csdp = None
        self._stack_file = ''
        self.set_stack_file(*stack_file)
        self.deadline = deadline
        self.followed_by = followed_by
        self.abort_on_miss = abort_on_miss
        self.list_activation_dates = list_activation_dates
        self.data = data
        self.preemption_cost = preemption_cost

    @property
    def csdp(self):
        """
        Accumulated Stack Distance Profile. Used by the cache models instead of
        the Stack Distance Profile for optimization matters.
        """
        return self._csdp

    @property
    def stack_file(self):
        """
        Stack distance profile input file.
        """
        return self._stack_file

    def set_stack_file(self, stack_file, cur_dir):
        """
        Set the stack distance profile.
        """
        if stack_file:
            try:
                self._stack = TaskInfo._parse_stack(stack_file)
                self._csdp = CSDP(self._stack)
                self._stack_file = os.path.relpath(stack_file, cur_dir)
            except Exception as e:
                print("set_stack_file failed:", e)

    @staticmethod
    def _parse_stack(stack_file):
        stack = {}
        if stack_file and os.path.isfile(stack_file):
            for line in open(stack_file):
                dist, value = line.split()
                stack[int(dist)] = float(value)
        else:
            stack = None
        return stack


class GenericTask(Process):
    """
    Abstract class for Tasks. :class:`ATask` and :class:`PTask` inherits from
    this class.

    These classes simulate the behavior of the simulated task. It controls the
    release of the jobs and is able to abort the jobs that exceed their
    deadline.

    The majority of the task_info attributes are available through this class
    too. A set of metrics such as the number of preemptions and migrations are
    available for analysis.
    """
    fields = []

    def __init__(self, sim, task_info):
        """
        Args:

        - `sim`: :class:`Model <simso.core.Model>` instance.
        - `task_info`: A :class:`TaskInfo` representing the Task.

        :type sim: Model
        :type task_info: TaskInfo
        """
        Process.__init__(self, name=task_info.name, sim=sim)
        self.name = task_info.name
        self._task_info = task_info
        self._monitor = Monitor(name="Monitor" + self.name + "_states",
                                sim=sim)
        self._activations_fifo = deque([])
        self._sim = sim
        self.cpu = None
        self._etm = sim.etm
        self._job_count = 0
        self._last_cpu = None
        self._cpi_alone = {}
        self._jobs = []
        self.job = None

    def __lt__(self, other):
        return self.identifier < other.identifier

    def is_active(self):
        return self.job is not None and self.job.is_active()

    def set_cpi_alone(self, proc, cpi):
        self._cpi_alone[proc] = cpi

    def get_cpi_alone(self, proc=None):
        if proc is None:
            proc = self.cpu
        return self._cpi_alone[proc]

    @property
    def base_cpi(self):
        return self._task_info.base_cpi

    @property
    def data(self):
        """
        Extra data to characterize the task. Only used by the scheduler.
        """
        return self._task_info.data

    @property
    def deadline(self):
        """
        Deadline in milliseconds.
        """
        return self._task_info.deadline

    @property
    def n_instr(self):
        return self._task_info.n_instr

    @property
    def mix(self):
        return self._task_info.mix

    @property
    def csdp(self):
        return self._task_info.csdp

    @property
    def preemption_cost(self):
        return self._task_info.preemption_cost

    @property
    def footprint(self):
        return int(self._task_info.n_instr * self._task_info.mix *
                   (1 - self._task_info.csdp.get(-1)))

    @property
    def wcet(self):
        """Worst-Case Execution Time in milliseconds."""
        return self._task_info.wcet

    @property
    def acet(self):
        return self._task_info.acet

    @property
    def et_stddev(self):
        return self._task_info.et_stddev

    @property
    def period(self):
        """
        Period of the task.
        """
        return self._task_info.period

    @property
    def identifier(self):
        """
        Identifier of the task.
        """
        return self._task_info.identifier

    @property
    def monitor(self):
        """
        The monitor for this Task. Similar to a log mechanism (see Monitor in
        SimPy doc).
        """
        return self._monitor

    @property
    def followed_by(self):
        """
        Task that is activated by the end of a job from this task.
        """
        if self._task_info.followed_by is not None:
            followed = [x for x in self._sim.task_list
                        if (x.identifier == self._task_info.followed_by)]
            if followed:
                return followed[0]
        return None

    @property
    def jobs(self):
        """
        List of the jobs.
        """
        return self._jobs

    def end_job(self, job):
        self._last_cpu = self.cpu
        if self.followed_by:
            self.followed_by.create_job(job)

        if len(self._activations_fifo) > 0:
            self._activations_fifo.popleft()
        if len(self._activations_fifo) > 0:
            self.job = self._activations_fifo[0]
            self.sim.activate(self.job, self.job.activate_job())

    def _job_killer(self, job):
        if job.end_date is None and job.computation_time < job.wcet:
            if self._task_info.abort_on_miss:
                self.cancel(job)
                job.abort()

    def create_job(self, pred=None):
        """
        Create a new job from this task. This should probably not be used
        directly by a scheduler.
        """
        self._job_count += 1
        job = Job(self, "{}_{}".format(self.name, self._job_count), pred,
                  monitor=self._monitor, etm=self._etm, sim=self.sim)

        if len(self._activations_fifo) == 0:
            self.job = job
            self.sim.activate(job, job.activate_job())
        self._activations_fifo.append(job)
        self._jobs.append(job)

        timer_deadline = Timer(self.sim, GenericTask._job_killer,
                               (self, job), self.deadline)
        timer_deadline.start()

    def _init(self):
        if self.cpu is None:
            self.cpu = self._sim.processors[0]


class ATask(GenericTask):
    """
    Non-periodic Task process. Inherits from :class:`GenericTask`. The job is
    created by another task.
    """
    fields = ['deadline', 'wcet']

    def execute(self):
        self._init()
        yield passivate, self


class PTask(GenericTask):
    """
    Periodic Task process. Inherits from :class:`GenericTask`. The jobs are
    created periodically.
    """
    fields = ['activation_date', 'period', 'deadline', 'wcet']

    def execute(self):
        self._init()
        # wait the activation date.
        yield hold, self, int(self._task_info.activation_date *
                              self._sim.cycles_per_ms)

        while True:
            #print self.sim.now(), "activate", self.name
            self.create_job()
            yield hold, self, int(self.period * self._sim.cycles_per_ms)


class SporadicTask(GenericTask):
    """
    Sporadic Task process. Inherits from :class:`GenericTask`. The jobs are
    created using a list of activation dates.
    """
    fields = ['list_activation_dates', 'deadline', 'wcet']

    def execute(self):

        self._init()
        for ndate in self.list_activation_dates:
            yield hold, self, int(ndate * self._sim.cycles_per_ms) \
                - self._sim.now()
            self.create_job()

    @property
    def list_activation_dates(self):
        return self._task_info.list_activation_dates


task_types = {
    "Periodic": PTask,
    "APeriodic": ATask,
    "Sporadic": SporadicTask
}

task_types_names = ["Periodic", "APeriodic", "Sporadic"]


def Task(sim, task_info):
    """
    Task factory. Return and instantiate the correct class according to the
    task_info.
    """

    return task_types[task_info.task_type](sim, task_info)
