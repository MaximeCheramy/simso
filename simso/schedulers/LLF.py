from simso.core import Scheduler, Timer
from simso.schedulers import scheduler

@scheduler("simso.schedulers.LLF")
class LLF(Scheduler):
    """Least Laxity First"""
    def init(self):
        self.ready_list = []
        self.timer = Timer(self.sim, LLF.update,
                           (self, self.processors[0]), 1, one_shot=False,
                           cpu=self.processors[0], overhead=.001)
        self.timer.start()

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
            self.ready_list.sort(key=lambda x: (x.laxity, x.task.identifier))

            # m : Nombre de processeurs.
            m = len(self.processors)

            # Available processors:
            l = (proc for proc in self.processors
                 if proc.running not in self.ready_list[:m])

            # The first m jobs should be running:
            for job in self.ready_list[:m]:
                if not job.is_running():
                    proc = next(l)
                    decisions.append((job, proc))

        return decisions
