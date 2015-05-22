"""
Partitionned EDF using PartitionedScheduler.
"""
from simso.core.Scheduler import SchedulerInfo
from simso.schedulers.EDF_mono import EDF_mono
from simso.utils import PartitionedScheduler
from simso.utils.PartitionedScheduler import decreasing_first_fit


class P_EDF(PartitionedScheduler):
    def init(self):
        PartitionedScheduler.init(
            self, SchedulerInfo("EDF_mono", EDF_mono), decreasing_first_fit)
