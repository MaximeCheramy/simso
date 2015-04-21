"""
Implementation of the Global-EDF (Earliest Deadline First) for multiprocessor
architectures.
"""
from simso.core import Scheduler


class EDF(Scheduler):
    """Earliest Deadline First"""
    def init(self):
        self.ready_list = []

    def on_activate(self, job):
        self.ready_list.append(job)
        job.cpu.resched()

    def on_terminated(self, job):
        if job in self.ready_list:
            self.ready_list.remove(job)
        else:
            job.cpu.resched()

    def schedule(self, cpu):
        ready_jobs = [j for j in self.ready_list if j.is_active()]

        if ready_jobs:
            # Key explanations:
            # First the free processors
            # Among the others, get the one with the greatest deadline
            # If equal, take the one used to schedule
            key = lambda x: (
                1 if not x.running else 0,
                x.running.absolute_deadline if x.running else 0,
                1 if x is cpu else 0
            )
            cpu_min = max(self.processors, key=key)

            job = min(ready_jobs, key=lambda x: x.absolute_deadline)

            if (cpu_min.running is None or
                    cpu_min.running.absolute_deadline > job.absolute_deadline):
                self.ready_list.remove(job)
                if cpu_min.running:
                    self.ready_list.append(cpu_min.running)
                return (job, cpu_min)
