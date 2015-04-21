"""
Implementation of the Global-Fair Lateness as presented by Erickson and
Anderson in Fair lateness scheduling: Reducing maximum lateness in G-EDF-like
scheduling.
"""
from simso.core import Scheduler


class G_FL(Scheduler):
    """Earliest Deadline First"""
    def init(self):
        self.ready_list = []

    def on_activate(self, job):
        job.priority = job.activation_date + job.deadline - \
            ((len(self.processors) - 1.0) / len(self.processors)) * job.wcet
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
                x.running.priority if x.running else 0,
                1 if x is cpu else 0
            )
            cpu_min = max(self.processors, key=key)

            job = min(ready_jobs, key=lambda x: x.priority)

            if (cpu_min.running is None or
                    cpu_min.running.priority > job.priority):
                self.ready_list.remove(job)
                if cpu_min.running:
                    self.ready_list.append(cpu_min.running)
                return (job, cpu_min)
