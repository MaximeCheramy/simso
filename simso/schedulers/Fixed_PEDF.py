#!/usr/bin/python
# coding=utf-8

from simso.core.Scheduler import SchedulerInfo
from simso.schedulers.EDF_mono import EDF_mono
from simso.utils import PartitionedScheduler


class Fixed_PEDF(PartitionedScheduler):
    def init(self):
        PartitionedScheduler.init(self, SchedulerInfo("EDF_mono", EDF_mono))

    def packer(self):
        for task in self.task_list:
            # Affect it to the task.
            cpu = next(proc for proc in self.processors
                       if proc.identifier == task.data["cpu"])
            self.affect_task_to_processor(task, cpu)
        return True
