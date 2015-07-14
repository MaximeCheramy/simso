"""
Work-Conserving version of U-EDF.
"""

from simso.schedulers.RUN import RUN
from simso.schedulers import scheduler

@scheduler("simso.schedulers.WC_RUN")
class WC_RUN(RUN):
    def init(self):
        RUN.init(self)
        self.state = {}

    def on_terminated(self, job):
        RUN.on_terminated(self, job)
        if job in self.state:
            del self.state[job]

    def on_abort(self, job):
        RUN.on_abort(self, job)
        if job in self.state:
            del self.state[job]

    def schedule(self, cpu):
        decisions = RUN.schedule(self, cpu)

#        print(".")
#        print([(id(job), job.name if job else None, proc.name)
#               for job, proc in self.state.items()])
#
#        print("decisions :")
#        print([(job.name if job else None, proc.name)
#               for job, proc in decisions])

        rstate = {proc: job for job, proc in self.state.items()}
        for djob, dproc in decisions:
            if dproc in rstate:
                del self.state[rstate[dproc]]
            if djob is not None:
                self.state[djob] = dproc
                rstate[dproc] = djob

#        print([(id(job), job.name if job else None, proc.name)
#               for job, proc in self.state.items()])

        running_jobs = list(self.state.keys())

        # Get active jobs.
        jobs = sorted(
            (task.job for task in self.task_list if task.job.is_active()),
            key=lambda j: j.absolute_deadline)

        # Bind jobs to processors:
        available_procs = list(self.processors)
        was_not_running = []
        for job in jobs:
            if job in running_jobs:
                available_procs.remove(self.state[job])
            else:
                was_not_running.append(job)

        remaining_jobs = []
        for job in was_not_running:
            if job.cpu in available_procs:
                decisions.append((job, job.cpu))
                available_procs.remove(job.cpu)
                self.state[job] = job.cpu
            else:
                remaining_jobs.append(job)

        for p, proc in enumerate(available_procs):
            if p < len(remaining_jobs):
                job = remaining_jobs[p]
                self.state[job] = proc
            else:
                job = None
            decisions.append((job, proc))

        return decisions
