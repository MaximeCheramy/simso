"""
Work-Conserving version of U-EDF.
"""

from simso.schedulers.U_EDF import U_EDF


class WC_U_EDF(U_EDF):
#    def on_terminated(self, job):
#        self.reschedule()
#
#    def on_aborted(self, job):
#        self.reschedule()

    def schedule(self, cpu):
        decisions = U_EDF.schedule(self, cpu)

        # Get active jobs.
        jobs = sorted(
            (task.job for task in self.task_list if task.job.is_active()),
            key=lambda j: j.absolute_deadline)

        # Bind jobs to processors:
        available_procs = list(self.processors)
        was_not_running = []
        for job in jobs:
            if job in self.running_jobs:
                for djob, dproc in decisions:
                    if djob == job:
                        available_procs.remove(dproc)
                        break
                else:
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

        try:
            for p, job in enumerate(remaining_jobs):
                decisions.append((job, available_procs[p]))
        except IndexError:
            pass

        return decisions
