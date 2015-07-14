"""
Cycle-Conserving EDF. A DVFS variant of EDF (uniprocessor).
"""
from simso.core import Scheduler
from simso.schedulers import scheduler

@scheduler("simso.schedulers.CC_EDF",
           required_proc_fields = [
               { 'name': 'speed', 'type': 'float', 'default': '1.0' }
           ]
)
class CC_EDF(Scheduler):
    def init(self):
        self.ready_list = []

        self.ui = {}
        for task in self.task_list:
            self.ui[task] = float(task.wcet) / task.period

        self.adjust_speed()

    def adjust_speed(self):
        # Compute processor speed
        utilization = min(1.0, sum(self.ui.values()))
        self.processors[0].set_speed(utilization)

    def on_activate(self, job):
        self.ui[job.task] = job.wcet / job.period
        self.ready_list.append(job)
        self.adjust_speed()
        job.cpu.resched()

    def on_terminated(self, job):
        self.ui[job.task] = job.actual_computation_time / job.period
        self.ready_list.remove(job)
        self.adjust_speed()
        job.cpu.resched()

    def schedule(self, cpu):
        if self.ready_list:
            # job with the highest priority
            job = min(self.ready_list, key=lambda x: x.absolute_deadline)
        else:
            job = None

        return (job, cpu)
