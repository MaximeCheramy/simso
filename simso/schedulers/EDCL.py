#!/usr/bin/python
# coding=utf-8
__author__ = 'Pierre-Emmanuel Hladik'


from simso.core import Scheduler
from simso.schedulers import scheduler

@scheduler("simso.schedulers.EDCL")
class EDCL(Scheduler):
    """
    EDCL Scheduler.
    Global EDF-based Scheduling with Efficient Priority Promotion.
    Shinpei Kato and Nobuyuki Yamasaki.
    The 14th International Conference on Embedded and Real-Time Computing
    Systems and Applications, 2008
    """
    def on_activate(self, job):
        job.cpu.resched()

    def on_terminated(self, job):
        job.cpu.resched()

    def update_laxity(self):
        for task in self.task_list:
            if task.is_active():
                job = task.job
                # if laxity is less than 0, the job will never respect its deadline,
                # so we do not consider this job as critical
                if job.laxity == 0:
                    job.data['priority'] = 0
                else:
                    job.data['priority'] = job.absolute_deadline

    def schedule(self, cpu):
        self.update_laxity()
        # List of ready jobs not currently running:
        ready_jobs = [t.job for t in self.task_list
                      if t.is_active() and not t.job.is_running()]

        if ready_jobs:
            # Select a free processor or, if none,
            # the one with the greatest deadline (self in case of equality):
            key = lambda x: (
                1 if not x.running else 0,
                x.running.absolute_deadline if x.running else 0,
                1 if x is cpu else 0
            )
            cpu_min = max(self.processors, key=key)

            # Select the job with the least priority:
            job = min(ready_jobs, key=lambda x: x.data['priority'])

            if (cpu_min.running is None or
                    cpu_min.running.absolute_deadline > job.absolute_deadline):
                return (job, cpu_min)
