from simso.core import Scheduler, Timer
from simso.core.Scheduler import SchedulerInfo
from fractions import Fraction
from math import ceil


class Modified_EDF(Scheduler):
    def init(self):
        self.ready_list = []

        self.migrating_task1 = None  # sous la forme (task, rate)
        self.migrating_task2 = None
        self.migrating_job1 = None
        self.migrating_job2 = None

        self.next_deadline = 0

    def on_activate(self, job):
        self.ready_list.append(job)
        job.cpu.resched()

    def on_terminated(self, job):
        self.ready_list.remove(job)
        job.cpu.resched()

    def conf(self, next_deadline):
        if next_deadline > self.next_deadline:
            self.next_deadline = next_deadline
            self.migrating_task1, self.migrating_task2 = \
                self.migrating_task2, self.migrating_task1
            if self.migrating_task1:
                time_a = ceil((next_deadline - self.sim.now())
                              * self.migrating_task1[1])
                self.timer_a = Timer(self.sim, Modified_EDF.on_end_migrating1,
                                     (self,), time_a, cpu=self.processors[0],
                                     in_ms=False)
                self.timer_a.start()

            self.migrating_job2 = None
            if self.migrating_task2:
                time_b = int((next_deadline - self.sim.now())
                             * (1 - self.migrating_task2[1]))
                self.timer_b = Timer(
                    self.sim, Modified_EDF.on_start_migrating2, (self,),
                    time_b, cpu=self.processors[0], in_ms=False)
                self.timer_b.start()
                self.processors[0].resched()

        if self.migrating_task1:
            self.migrating_job1 = self.migrating_task1[0].job
            self.processors[0].resched()
        else:
            self.migrating_job1 = None

    def on_end_migrating1(self):
        self.migrating_job1 = None
        self.processors[0].resched()

    def on_start_migrating2(self):
        self.migrating_job2 = self.migrating_task2[0].job
        self.processors[0].resched()

    def schedule(self, cpu):
        if self.migrating_job1 and self.migrating_job1.is_active():
            return (self.migrating_job1, cpu)
        if self.migrating_job2 and self.migrating_job2.is_active():
            return (self.migrating_job2, cpu)

        if self.ready_list:
            job = min(self.ready_list, key=lambda x: x.absolute_deadline)
        else:
            job = None

        return (job, cpu)


class Group(object):
    def __init__(self, sim):
        self.tasks = []
        self.schedulers = []
        self.sim = sim

    def compute_next_deadline(self):
        return min([task.jobs[-1].absolute_deadline
                    for task in self.tasks if task.jobs]) \
            * self.sim.cycles_per_ms


class EKG(Scheduler):
    def init(self):
        self.groups = []
        self.task_to_group = {}
        try:
            k = self.data['K']
        except KeyError:
            k = len(self.processors)
        m = len(self.processors)

        sep = Fraction(k) / Fraction(1 + k) if k < m else 1

        light_tasks = [t for t in self.task_list if t.wcet < sep * t.period]
        heavy_tasks = [t for t in self.task_list if t.wcet >= sep * t.period]

        # Mapping task to scheduler.
        self.map_task_sched = {}
        self.map_cpu_sched = {}

        cpus = []
        for i, cpu in enumerate(self.processors):
            # Instantiate a scheduler.
            sched = Modified_EDF(self.sim, SchedulerInfo("Modified_EDF",
                                                         Modified_EDF))
            sched.add_processor(cpu)
            sched.init()

            # Append the processor to a list with an initial utilization of 0.
            cpus.append([cpu, sched, Fraction(0)])

            # Affect the scheduler to the processor.
            self.map_cpu_sched[cpu.identifier] = sched

            # Affect to the correct group.
            if i >= len(heavy_tasks):
                if (i - len(heavy_tasks)) % k == 0:
                    group = Group(self.sim)
                    group.schedulers.append(sched)
                    self.groups.append(group)
                else:
                    self.groups[-1].schedulers.append(sched)

        # Affect heavy tasks to individual processors.
        p = 0
        for task in heavy_tasks:
            cpu, sched, _ = cpus[p]

            # Affect the task to the processor.
            self.map_task_sched[task.identifier] = sched
            sched.add_task(task)

            # Put the task on that processor.
            task.cpu = cpu
            p += 1

            self.task_to_group[task] = None

        # Custom Next Fit
        for task in light_tasks:
            g = (p - len(heavy_tasks)) // k
            if cpus[p][2] + Fraction(task.wcet) / Fraction(task.period) <= 1.0:
                cpu, sched, _ = cpus[p]
                # Affect the task to the processors.
                self.map_task_sched[task.identifier] = sched
                sched.add_task(task)

                # Put the task on that processor.
                task.cpu = cpu

                cpus[p][2] += Fraction(task.wcet) / Fraction(task.period)

                self.groups[g].tasks.append(task)
                self.task_to_group[task] = self.groups[g]

                if cpus[p][2] == 1:
                    p += 1
            else:
                if (p + 1 - len(heavy_tasks)) % k == 0:
                    cpu, sched, _ = cpus[p + 1]
                    # Affect the task to the processor.
                    self.map_task_sched[task.identifier] = sched
                    sched.add_task(task)

                    # Put the task on that processor.
                    task.cpu = cpu

                    cpus[p + 1][2] += \
                        Fraction(task.wcet) / Fraction(task.period)
                    self.groups[g + 1].tasks.append(task)
                    self.task_to_group[task] = self.groups[g + 1]
                else:
                    # Split in 2.
                    u1 = 1 - cpus[p][2]
                    u2 = Fraction(task.wcet) / Fraction(task.period) - u1
                    cpus[p][1].migrating_task2 = (task, u1)
                    cpus[p + 1][1].migrating_task1 = (task, u2)
                    cpus[p + 1][2] = u2
                    self.groups[g].tasks.append(task)
                    self.task_to_group[task] = self.groups[g]

                p += 1

    def schedule(self, cpu):
        return self.map_cpu_sched[cpu.identifier].schedule(cpu)

    def on_activate(self, job):
        group = self.task_to_group[job.task]
        if group:
            nd = group.compute_next_deadline()
            for sched in group.schedulers:
                sched.conf(nd)
        try:
            self.map_task_sched[job.task.identifier].on_activate(job)
        except KeyError:
            job.cpu.resched()

    def on_terminated(self, job):
        try:
            self.map_task_sched[job.task.identifier].on_terminated(job)
        except KeyError:
            job.cpu.resched()
