#!/usr/bin/python
# coding=utf-8

import os
import re
from xml.dom import minidom
from simso.core.Scheduler import SchedulerInfo
from simso.core import Scheduler
from simso.core.Task import TaskInfo
from simso.core.Processor import ProcInfo

from .GenerateConfiguration import generate
from .parser import Parser


# Hack for Python2
if not hasattr(minidom.NamedNodeMap, '__contains__'):
    minidom.NamedNodeMap.__contains__ = minidom.NamedNodeMap.has_key


def _gcd(*numbers):
    """Return the greatest common divisor of the given integers"""
    from fractions import gcd
    return reduce(gcd, numbers)


# Least common multiple is not in standard libraries?
def _lcm(numbers):
    """Return lowest common multiple."""
    def lcm(a, b):
        return (a * b) // _gcd(a, b)
    return reduce(lcm, numbers, 1)


class Configuration(object):
    """
    The configuration class store all the details about a system. An instance
    of this class will be passed to the constructor of the
    :class:`Model <simso.core.Model.Model>` class.
    """
    def __init__(self, filename=None):
        """
        Args:
            - `filename` A file can be used to initialize the configuration.
        """
        if filename:
            parser = Parser(filename)
            self.etm = parser.etm
            self.duration = parser.duration
            self.cycles_per_ms = parser.cycles_per_ms
            self._caches_list = parser.caches_list
            self.memory_access_time = parser.memory_access_time
            self._task_info_list = parser.task_info_list
            self.task_data_fields = parser.task_data_fields
            self._proc_info_list = parser.proc_info_list
            self.proc_data_fields = parser.proc_data_fields
            self._scheduler_info = parser.scheduler_info
            self.penalty_preemption = parser.penalty_preemption
            self.penalty_migration = parser.penalty_migration
        else:
            self.etm = "wcet"
            self.duration = 100000000
            self.penalty_preemption = 0
            self.penalty_migration = 0
            self.cycles_per_ms = 1000000
            self._caches_list = []
            self._task_info_list = []
            self.task_data_fields = {}
            self._proc_info_list = []
            self.proc_data_fields = {}
            self.memory_access_time = 100
            self._scheduler_info = SchedulerInfo()
        self.calc_penalty_cache()
        self._set_filename(filename)

    def _set_filename(self, filename):
        self._simulation_file = filename
        if filename:
            self._cur_dir = os.path.split(filename)[0]
            if not self._cur_dir:
                self._cur_dir = os.curdir
        else:
            self._cur_dir = os.curdir

    def save(self, simulation_file=None):
        """
        Save the current configuration in a file. If no file is given as
        argument, the previous file used to write or read the configuration is
        used again.
        """
        if simulation_file:
            old_dir = self._cur_dir
            self._cur_dir = os.path.split(simulation_file)[0] or '.'

            # Update relative paths.
            self._scheduler_info.set_name(
                old_dir + '/' + self._scheduler_info.name, self._cur_dir)
            for task in self._task_info_list:
                if task.stack_file:
                    task.set_stack_file(
                        old_dir + '/' + task.stack_file, self._cur_dir)

            self._simulation_file = simulation_file

        conf_file = open(self._simulation_file, 'w')
        conf_file.write(generate(self))

    def calc_penalty_cache(self):
        for proc in self.proc_info_list:
            access_time = self.memory_access_time
            for cache in reversed(proc.caches):
                cache.penalty = access_time - cache.access_time
                access_time = cache.access_time

            proc.penalty = access_time

    def check_all(self):
        """
        Check the correctness of the configuration (without simulating it).
        """
        self.check_general()
        self.check_scheduler()
        self.check_processors()
        self.check_tasks()
        self.check_caches()

    def check_general(self):
        assert self.duration >= 0, \
            "Simulation duration must be a positive number."
        assert self.cycles_per_ms >= 0, \
            "Cycles / ms must be a positive number."
        assert self.memory_access_time >= 0, \
            "The memory access time must be a positive number."

    def check_scheduler(self):
        cls = self._scheduler_info.get_cls()
        assert cls is not None, \
            "A scheduler is needed."
        assert issubclass(cls, Scheduler), \
            "Must inherits from Scheduler."
        assert self._scheduler_info.overhead >= 0, \
            "An overhead must not be negative."

    def check_processors(self):
        # At least one processor:
        assert len(self._proc_info_list) > 0, \
            "At least one processor is needed."

        # Caches inclusifs :
        succ = {}
        for proc in self._proc_info_list:
            cur = None
            for cache in reversed(proc.caches):
                assert not (cache in succ and succ[cache] != cur), \
                    "Caches must be inclusives."
                succ[cache] = cur
                cur = cache

        for index, proc in enumerate(self._proc_info_list):
            # Nom correct :
            assert re.match('^[a-zA-Z][a-zA-Z0-9 _-]*$', proc.name), \
                "A processor name must begins with a letter and must not "\
                "contains any special character."
            # Id unique :
            assert proc.identifier not in [
                x.identifier for x in self._proc_info_list[index + 1:]], \
                "Processors' identifiers must be uniques."

            # Overheads positifs :
            assert proc.cs_overhead >= 0, \
                "Context Save overhead can't be negative."
            assert proc.cl_overhead >= 0, \
                "Context Load overhead can't be negative."

    def check_tasks(self):
        assert len(self._task_info_list) > 0, "At least one task is needed."
        for index, task in enumerate(self._task_info_list):
            # Id unique :
            assert task.identifier not in [
                x.identifier for x in self._task_info_list[index + 1:]], \
                "Tasks' identifiers must be uniques."
            # Nom correct :
            assert re.match('^[a-zA-Z][a-zA-Z0-9 _-]*$', task.name), "A task "\
                "name must begins with a letter and must not contains any "\
                "special character."

            # Activation date >= 0:
            assert task.activation_date >= 0, \
                "Activation date must be positive."

            # Period >= 0:
            assert task.period >= 0, "Tasks' periods must be positives."

            # Deadline >= 0:
            assert task.deadline >= 0, "Tasks' deadlines must be positives."

            # N_instr >= 0:
            assert task.n_instr >= 0, \
                "A number of instructions must be positive."

            # WCET >= 0:
            assert task.wcet >= 0, "WCET must be positive."

            # ACET >= 0:
            assert task.acet >= 0, "ACET must be positive."

            # ET-STDDEV >= 0:
            assert task.et_stddev >= 0, \
                "A standard deviation is a positive number."

            # mix in [0.0, 2.0]
            assert 0.0 <= task.mix <= 2.0, \
                "A mix must be positive and less or equal than 2.0"

            if self.etm == "cache":
                # stack
                assert task.stack_file, "A task needs a stack profile."

                # stack ok
                assert task.csdp, "Stack not found or empty."

    def check_caches(self):
        for index, cache in enumerate(self._caches_list):
            # Id unique :
            assert cache.identifier not in [
                x.identifier for x in self._caches_list[index + 1:]], \
                "Caches' identifiers must be uniques."

            # Nom correct :
            assert re.match('^[a-zA-Z][a-zA-Z0-9_-]*$', cache.name), \
                "A cache name must begins with a letter and must not " \
                "contains any spacial character nor space."

            # Taille positive :
            assert cache.size >= 0, "A cache size must be positive."

            # Access time >= 0:
            assert cache.access_time >= 0, "An access time must be positive."

    def get_hyperperiod(self):
        """
        Compute and return the hyperperiod of the tasks.
        """
        return _lcm([x.period for x in self.task_info_list])

    @property
    def duration_ms(self):
        return self.duration / self.cycles_per_ms

    @property
    def simulation_file(self):
        return self._simulation_file

    @property
    def cur_dir(self):
        return self._cur_dir

    @property
    def caches_list(self):
        return self._caches_list

    @property
    def task_info_list(self):
        """
        List of tasks (TaskInfo objects).
        """
        return self._task_info_list

    @property
    def proc_info_list(self):
        """
        List of processors (ProcInfo objects).
        """
        return self._proc_info_list

    @property
    def scheduler_info(self):
        """
        SchedulerInfo object.
        """
        return self._scheduler_info

    def add_task(self, name, identifier, task_type="Periodic",
                 abort_on_miss=False, period=10, activation_date=0,
                 n_instr=0, mix=0.5, stack_file="", wcet=0, acet=0,
                 et_stddev=0, deadline=10, base_cpi=1.0, followed_by=None,
                 list_activation_dates=[], preemption_cost=0, data=None):
        """
        Helper method to create a TaskInfo and add it to the list of tasks.
        """
        if data is None:
            data = dict((k, None) for k in self.task_data_fields)

        task = TaskInfo(name, identifier, task_type, abort_on_miss, period,
                        activation_date, n_instr, mix,
                        (stack_file, self.cur_dir), wcet, acet, et_stddev,
                        deadline, base_cpi, followed_by, list_activation_dates,
                        preemption_cost, data)
        self.task_info_list.append(task)
        return task

    def add_processor(self, name, identifier, cs_overhead=0,
                      cl_overhead=0, migration_overhead=0, speed=1.0):
        """
        Helper method to create a ProcInfo and add it to the list of
        processors.
        """
        proc = ProcInfo(
            identifier, name, cs_overhead, cl_overhead, migration_overhead,
            speed)
        self.proc_info_list.append(proc)
        return proc
