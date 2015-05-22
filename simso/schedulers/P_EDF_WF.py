"""
Partitionned EDF using PartitionedScheduler.
"""
from simso.core.Scheduler import SchedulerInfo
from simso.schedulers.EDF_mono import EDF_mono
from simso.utils import PartitionedScheduler
from simso.utils.PartitionedScheduler import decreasing_worst_fit


class P_EDF_WF(PartitionedScheduler):
    def init(self):
        PartitionedScheduler.init(
            self, SchedulerInfo("EDF_mono", EDF_mono), decreasing_worst_fit)
