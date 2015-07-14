#!/usr/bin/python
# coding=utf-8

from simso.core import Scheduler, Timer
from simso.schedulers import scheduler

@scheduler("simso.schedulers.EDZL")
class EDZL(Scheduler):
    """
    EDZL Scheduler. EDF Scheduler with zero laxity events.
    """

    def init(self):
        self.ready_list = []
        self.zl_timer = None

    def on_activate(self, job):
        job.priority = job.absolute_deadline
        self.ready_list.append(job)
        job.cpu.resched()

    def on_terminated(self, job):
        # ce test est peut-être utile en cas d'avortement de tâche.
        if job in self.ready_list:
            self.ready_list.remove(job)
        if self.zl_timer and job == self.zl_timer[0]:
            self.zl_timer[1].stop()
        job.cpu.resched()

    def zero_laxity(self, job):
        if job in self.ready_list:
            job.priority = 0
            job.cpu.resched()
        else:
            print(self.sim.now(), job.name)

    def schedule(self, cpu):
        """
        Basically a EDF scheduling but using a priority attribute.
        """
        ready_jobs = [j for j in self.ready_list if j.is_active()]
        if ready_jobs:
            selected_job = None

            key = lambda x: (
                1 if x.running else -1,
                -x.running.priority if x.running else 0,
                -1 if x is cpu else 1)
            cpu_min = min(self.processors, key=key)

            job = min(ready_jobs, key=lambda x: x.priority)
            if cpu_min.running is None or \
                    cpu_min.running.priority > job.priority:
                self.ready_list.remove(job)
                if cpu_min.running:
                    self.ready_list.append(cpu_min.running)
                selected_job = (job, cpu_min)

            # Recherche du prochain event ZeroLaxity pour configurer le timer.
            minimum = None
            for job in self.ready_list:
                zl_date = job.laxity
                if (minimum is None or minimum[0] > zl_date) and zl_date > 0:
                    minimum = (zl_date, job)

            if self.zl_timer:
                self.zl_timer[1].stop()
            if minimum:
                self.zl_timer = (minimum[0], Timer(
                    self.sim, EDZL.zero_laxity, (self, minimum[1]),
                    minimum[0], cpu=cpu, in_ms=False))
                self.zl_timer[1].start()

            return selected_job
