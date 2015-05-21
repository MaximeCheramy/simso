"""
Static EDF. A DVFS variant of EDF (uniprocessor).
"""
from simso.core import Scheduler


class Static_EDF(Scheduler):
    def init(self):
        self.ready_list = []
        # Compute processor speed
        utilization = sum([t.wcet / t.period for t in self.task_list], 0.0)
        self.processors[0].set_speed(utilization)

    def on_activate(self, job):
        self.ready_list.append(job)
        job.cpu.resched()

    def on_terminated(self, job):
        self.ready_list.remove(job)
        job.cpu.resched()

    def schedule(self, cpu):
        if self.ready_list:
            # job with the highest priority
            job = min(self.ready_list, key=lambda x: x.absolute_deadline)
        else:
            job = None

        return (job, cpu)
