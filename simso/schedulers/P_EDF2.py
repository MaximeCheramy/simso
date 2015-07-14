"""
Partitionned EDF without the helping class.

Use EDF_mono.
"""
from simso.core import Scheduler
from simso.core.Scheduler import SchedulerInfo
from simso.schedulers.EDF_mono import EDF_mono
from simso.schedulers import scheduler

@scheduler("simso.schedulers.P_EDF2")
class P_EDF2(Scheduler):
    def init(self):
        # Mapping processor to scheduler.
        self.map_cpu_sched = {}
        # Mapping task to scheduler.
        self.map_task_sched = {}

        cpus = []
        for cpu in self.processors:
            # Append the processor to a list with an initial utilization of 0.
            cpus.append([cpu, 0])

            # Instantiate a scheduler.
            sched = EDF_mono(self.sim, SchedulerInfo("simso.schedulers.EDF_mono"))
            sched.add_processor(cpu)
            sched.init()

            # Affect the scheduler to the processor.
            self.map_cpu_sched[cpu.identifier] = sched

        # First Fit
        for task in self.task_list:
            j = 0
            # Find a processor with free space.
            while cpus[j][1] + float(task.wcet) / task.period > 1.0:
                j += 1
                if j >= len(self.processors):
                    print("oops bin packing failed.")
                    return

            # Get the scheduler for this processor.
            sched = self.map_cpu_sched[cpus[j][0].identifier]

            # Affect it to the task.
            self.map_task_sched[task.identifier] = sched
            sched.add_task(task)

            # Put the task on that processor.
            task.cpu = cpus[j][0]
            self.sim.logger.log("task " + task.name + " on " + task.cpu.name)

            # Update utilization.
            cpus[j][1] += float(task.wcet) / task.period

    def get_lock(self):
        # No lock mechanism is needed.
        return True

    def schedule(self, cpu):
        return self.map_cpu_sched[cpu.identifier].schedule(cpu)

    def on_activate(self, job):
        self.map_task_sched[job.task.identifier].on_activate(job)

    def on_terminated(self, job):
        self.map_task_sched[job.task.identifier].on_terminated(job)
