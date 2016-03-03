from simso.core import Scheduler, Timer
from simso.schedulers import scheduler

@scheduler("simso.schedulers.MLLF")
class MLLF(Scheduler):
    """Modified Least Laxity First"""
    def init(self):
        self.ready_list = []
        self.timer = None

    def update(self, cpu):
        if self.ready_list:
            cpu.resched()

    def on_activate(self, job):
        self.ready_list.append(job)
        job.cpu.resched()

    def on_terminated(self, job):
        self.ready_list.remove(job)
        self.update(job.cpu)

    def schedule(self, cpu):
        decisions = []
        if self.ready_list:
            # Sort according to the laxity.
            self.ready_list.sort(
                key=lambda x: (x.laxity, x.absolute_deadline))

            # m : Nombre de processeurs.
            m = len(self.processors)

            # Available processors:
            l = (proc for proc in self.processors
                 if proc.running not in self.ready_list[:m])

            if len(self.ready_list) > m:
                ta = self.ready_list[m - 1]
                dmin = self.ready_list[m].absolute_deadline * \
                    self.sim.cycles_per_ms - self.sim.now()

                if self.timer:
                    self.timer.stop()
                self.timer = Timer(
                    self.sim, MLLF.update,
                    (self, self.processors[0]), dmin - ta.laxity,
                    one_shot=True,
                    cpu=self.processors[0])
                self.timer.start()

            # The first m jobs should be running:
            for job in self.ready_list[:m]:
                if not job.is_running():
                    proc = next(l)
                    decisions.append((job, proc))

        return decisions
