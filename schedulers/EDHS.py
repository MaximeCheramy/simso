"""
Implementation of the EDHS Scheduler.

EDHS is a semi-partitionned scheduler proposed by Kato et al in
"Semi-Partitioning Technique for Multiprocessor Real-Time Scheduling".
"""
from simso.core import Scheduler, Timer
from simso.core.Scheduler import SchedulerInfo
from fractions import Fraction
from math import ceil

migrating_tasks = {}

# Mapping processor to scheduler.
map_cpu_sched = {}


class EDF_modified(Scheduler):
    """
    An EDF mono-processor scheduler modified to accept migrating jobs.
    A migrating job has an infinite priority.
    """
    def init(self):
        self.ready_list = []
        self.migrating_job = None

    def _resched(self):
        self.processors[0].resched()

    def on_activate(self, job):
        self.ready_list.append(job)
        self._resched()

    def on_terminated(self, job):
        if job is self.migrating_job:
            self.migrating_job = None
        elif job in self.ready_list:
            self.ready_list.remove(job)
        self._resched()

    def accept_migrating_job(self, i, job, budget):
        self.migrating_job = job
        job.task.cpu = self.processors[0]

        # Set timer for end.
        self.timer = Timer(self.sim, EDF_modified.end_migrating_job,
                           (self, i), budget, cpu=self.processors[0],
                           in_ms=False)
        self.timer.start()

        self._resched()

    def end_migrating_job(self, i):
        self.processors[0].resched()
        if self.migrating_job and i < len(migrating_tasks[self.migrating_job.task]) - 1:
            ncpu, nbudget = migrating_tasks[self.migrating_job.task][i + 1]
            sched = map_cpu_sched[ncpu]
            sched.accept_migrating_job(i + 1, self.migrating_job, nbudget)
        self.migrating_job = None

    def schedule(self, cpu):
        if self.migrating_job:
            job = self.migrating_job
        elif self.ready_list:
            job = min(self.ready_list, key=lambda x: x.absolute_deadline)
        else:
            job = None

        return (job, cpu)


class EDHS(Scheduler):
    def init(self):
        # Mapping task to scheduler.
        self.map_task_sched = {}

        cpus = []
        for cpu in self.processors:
            # Append the processor to a list with an initial utilization of 0.
            cpus.append([cpu, Fraction(0)])

            # Instantiate a scheduler.
            sched = EDF_modified(self.sim, SchedulerInfo("EDF_modified",
                                 EDF_modified))
            sched.add_processor(cpu)
            sched.init()

            # Affect the scheduler to the processor.
            map_cpu_sched[cpu] = sched

        # First Fit
        for task in self.task_list:
            j = 0
            # Find a processor with free space.
            while cpus[j][1] + Fraction(task.wcet) / Fraction(task.period) > 1.0:
                j += 1
                if j >= len(self.processors):
                    migrating_tasks[task] = []
                    break
            if j == len(self.processors):
                continue

            # Get the scheduler for this processor.
            sched = map_cpu_sched[cpus[j][0]]

            # Affect it to the task.
            self.map_task_sched[task.identifier] = sched
            sched.add_task(task)

            # Put the task on that processor.
            task.cpu = cpus[j][0]
            self.sim.logger.log("task " + task.name + " on " + task.cpu.name)

            # Update utilization.
            cpus[j][1] += Fraction(task.wcet) / Fraction(task.period)

        for task, l in migrating_tasks.items():
            rem = Fraction(task.wcet) / Fraction(task.period)
            for cpu, cpu_u in cpus:
                if cpu_u < 1 and rem > 0:
                    u = min(rem, 1 - cpu_u)
                    l.append((cpu, ceil(u * task.period * self.sim.cycles_per_ms)))
                    rem -= u

    def get_lock(self):
        # No lock mechanism is needed.
        return True

    def schedule(self, cpu):
        return map_cpu_sched[cpu].schedule(cpu)

    def on_activate(self, job):
        try:
            self.map_task_sched[job.task.identifier].on_activate(job)
        except KeyError:
            cpu, budget = migrating_tasks[job.task][0]
            sched = map_cpu_sched[cpu]
            sched.accept_migrating_job(0, job, budget)

    def on_terminated(self, job):
        try:
            self.map_task_sched[job.task.identifier].on_terminated(job)
        except KeyError:
            sched = map_cpu_sched[job.task.cpu]
            sched.on_terminated(job)
