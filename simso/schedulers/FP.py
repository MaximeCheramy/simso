#!/usr/bin/python
# coding=utf-8

from simso.core import Scheduler
from simso.schedulers import scheduler

@scheduler("simso.schedulers.FP", 
    required_task_fields = [
        {'name': 'priority', 'type' : 'int', 'default' : '0' }   
    ]
)
class FP(Scheduler):
    """ Fixed Priority (use 'priority' field) """
    def init(self):
        self.ready_list = []

    def on_activate(self, job):
        self.ready_list.append(job)
        job.cpu.resched()

    def on_terminated(self, job):
        job.cpu.resched()

    def schedule(self, cpu):
        if self.ready_list:
            # Get a free processor or a processor running a low priority job.
            key = lambda x: (
                1 if x.running else 0,
                x.running.data['priority'] if x.running else 0,
                0 if x is cpu else 1
            )
            cpu_min = min(self.processors, key=key)

            # Get the job with the highest priority.
            job = max(self.ready_list, key=lambda x: x.data['priority'])

            if (cpu_min.running is None or
                    cpu_min.running.data['priority'] < job.data['priority']):
                self.ready_list.remove(job)
                if cpu_min.running:
                    self.ready_list.append(cpu_min.running)
                return (job, cpu_min)

        return None
