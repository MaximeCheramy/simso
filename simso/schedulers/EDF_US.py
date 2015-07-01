"""
Implementation of EDF-US[1/2].
"""
from simso.core import Scheduler
from simso.schedulers import scheduler

@scheduler("simso.schedulers.EDF_US")
class EDF_US(Scheduler):
    def init(self):
        self.ready_list = []

    def on_activate(self, job):
        if job.wcet > job.period / 2:
            job.priority = 0
        else:
            job.priority = job.absolute_deadline
        self.ready_list.append(job)
        job.cpu.resched()

    def on_terminated(self, job):
        if job in self.ready_list:
            self.ready_list.remove(job)
        else:
            job.cpu.resched()

    def schedule(self, cpu):
        if self.ready_list:
            # Key explanations:
            # First the free processors
            # Among the others, get the one with the greatest deadline
            # If equal, take the one used to schedule
            key = lambda x: (
                1 if not x.running else 0,
                x.running.priority if x.running else 0,
                1 if x is cpu else 0
            )
            cpu_min = max(self.processors, key=key)

            job = min([j for j in self.ready_list if j.is_active()],
                      key=lambda x: x.priority)

            if (cpu_min.running is None or
                    cpu_min.running.priority > job.priority):
                self.ready_list.remove(job)
                if cpu_min.running:
                    self.ready_list.append(cpu_min.running)
                return (job, cpu_min)
