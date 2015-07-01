from simso.core import Scheduler, Timer
from simso.schedulers import scheduler

@scheduler("simso.schedulers.G_FL_ZL")
class G_FL_ZL(Scheduler):
    """
    G_FL with Zero Laxity Scheduler.
    """

    def init(self):
        self.ready_list = []
        self.zl_timer = None

    def on_activate(self, job):
        job.priority = job.activation_date + job.deadline - \
                       ((len(self.processors) - 1.0) / len(self.processors)) * job.wcet
        self.ready_list.append(job)
        job.cpu.resched()

    def on_terminated(self, job):
        if job in self.ready_list:
            self.ready_list.remove(job)
        if self.zl_timer and job == self.zl_timer[0]:
            self.zl_timer[1].stop()
        job.cpu.resched()

    def zero_laxity(self, job):
        if job in self.ready_list:
            job.priority = 0
            job.cpu.resched()
        else:
            print(self.sim.now(), job.name)

    def schedule(self, cpu):
        """
        Basically a EDF scheduling but using a priority attribute.
        """
        if self.ready_list:
            selected_job = None

            key = lambda x: (
                1 if x.running else -1,
                -x.running.priority if x.running else 0,
                -1 if x is cpu else 1)
            cpu_min = min(self.processors, key=key)

            job = min(self.ready_list, key=lambda x: x.priority)
            if cpu_min.running is None or \
                    cpu_min.running.priority > job.priority:
                self.ready_list.remove(job)
                if cpu_min.running:
                    self.ready_list.append(cpu_min.running)
                selected_job = (job, cpu_min)

            minimum = None
            for job in self.ready_list:
                zl_date = int((job.absolute_deadline - job.ret
                               ) * self.sim.cycles_per_ms - self.sim.now())
                if (minimum is None or minimum[0] > zl_date) and zl_date > 0:
                    minimum = (zl_date, job)

            if self.zl_timer:
                self.zl_timer[1].stop()
            if minimum:
                self.zl_timer = (minimum[0], Timer(
                    self.sim, G_FL_ZL.zero_laxity, (self, minimum[1]),
                    minimum[0], cpu=cpu, in_ms=False))
                self.zl_timer[1].start()

            return selected_job
