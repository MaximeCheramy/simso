from simso.core import Scheduler


class RM(Scheduler):
    """ Rate monotonic """
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
        decision = None
        if self.ready_list:
            # Get a free processor or a processor running a low priority job.
            key = lambda x: (
                0 if x.running is None else 1,
                -x.running.period if x.running else 0,
                0 if x is cpu else 1
            )
            cpu_min = min(self.processors, key=key)

            # Job with highest priority.
            job = min(self.ready_list, key=lambda x: x.period)

            if (cpu_min.running is None or
                    cpu_min.running.period > job.period):
                self.ready_list.remove(job)
                if cpu_min.running:
                    self.ready_list.append(cpu_min.running)
                decision = (job, cpu_min)

        return decision
