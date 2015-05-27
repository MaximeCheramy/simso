"""
Implementation of the Global-EDF (Earliest Deadline First) for multiprocessor
architectures (alternative implementation as the one provided by EDF.py).
"""
from simso.core import Scheduler


class EDF2(Scheduler):
    """Earliest Deadline First"""
    def init(self):
        self.running_jobs = []
        self.sched_to_do = False

    def on_activate(self, job):
        self.resched(job.cpu)

    def on_terminated(self, job):
        self.resched(job.cpu)

    def resched(self, cpu):
        if not self.sched_to_do:
            cpu.resched()
        self.sched_to_do = True

    def schedule(self, cpu):
        self.sched_to_do = False
        decisions = []

        ready_jobs = sorted(
            [t.job for t in self.task_list if t.job.is_active()],
            key=lambda x: x.absolute_deadline)
        jobs = ready_jobs[:len(self.processors)]

        # Bind jobs to processors:
        available_procs = list(self.processors)
        was_not_running = []
        for job in jobs:
            if job in self.running_jobs:
                available_procs.remove(job.cpu)
            else:
                was_not_running.append(job)

        remaining_jobs = []
        for job in was_not_running:
            if job.cpu in available_procs:
                decisions.append((job, job.cpu))
                available_procs.remove(job.cpu)
            else:
                remaining_jobs.append(job)

        for p, job in enumerate(remaining_jobs):
            decisions.append((job, available_procs[p]))

        self.running_jobs = jobs

        return decisions
