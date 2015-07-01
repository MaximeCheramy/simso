# coding=utf-8

from simso.core import Scheduler, Timer
from math import ceil
from simso.schedulers import scheduler

@scheduler("simso.schedulers.EPDF")
class EPDF(Scheduler):
    """Earliest Pseudo-Deadline First"""

    quantum = 1  # ms

    class PseudoJob(object):
        def __init__(self, job, seq):
            self.job = job
            self.release_date = int((seq - 1) / (job.wcet / job.deadline))
            self.deadline = int(ceil(seq / (job.wcet / job.deadline)))
            self.seq = seq

        def cmp_key(self):
            return self.deadline * EPDF.quantum + self.job.activation_date

    def init(self):
        self.ready_list = []
        self.pseudo_job = {}
        self.timers = []

    def pseudo_terminate(self, pseudo_job):
        if self.pseudo_job[pseudo_job.job.cpu] == pseudo_job:
            self.pseudo_job[pseudo_job.job.cpu] = None
            pseudo_job.job.cpu.resched()

    def pseudo_activate(self, pseudo_job):
        pseudo_job.job.cpu.resched()
        self.ready_list.append(pseudo_job)

    def on_activate(self, job):
        # First pseudo-activation
        pseudo_job = EPDF.PseudoJob(job, 1)

        self.pseudo_activate(pseudo_job)

        # Set next pseudo activations :
        while pseudo_job.seq * self.quantum < job.wcet:
            pseudo_job = EPDF.PseudoJob(job, pseudo_job.seq + 1)
            timer = Timer(self.sim, EPDF.pseudo_activate, (self, pseudo_job),
                          pseudo_job.release_date * self.quantum -
                          self.sim.now() / self.sim.cycles_per_ms +
                          job.activation_date, cpu=job.cpu,
                          in_ms=True)
            timer.start()
            self.timers.append(timer)

    def on_terminated(self, job):
        self.ready_list = [x for x in self.ready_list if x.job is not job]

    def schedule(self, cpu):
        if len(self.ready_list) > 0:
            # Explication sur la key:
            # En priorité, on met tous les processeurs libres au début.
            # Ensuite, on trie tout par ordre décroissant de la deadline.
            # Et on départage en préférant le processeur "cpu".
            key = lambda x: (
                1 if (not x.running) or (not self.pseudo_job[x]) else 0,
                self.pseudo_job[x].cmp_key() if x.running and
                self.pseudo_job[x] else None,
                1 if x is cpu else 0
            )
            cpu_min = max(self.processors, key=key)

            pjob = min(self.ready_list, key=lambda x: x.cmp_key())

            if (cpu_min.running is None or
                    self.pseudo_job[cpu_min] is None or
                    self.pseudo_job[cpu_min].cmp_key() > pjob.cmp_key()):
                self.ready_list.remove(pjob)
                if cpu_min.running and self.pseudo_job[cpu_min]:
                    self.ready_list.append(self.pseudo_job[cpu_min])
                self.pseudo_job[cpu_min] = pjob

                timer = Timer(
                    self.sim, EPDF.pseudo_terminate, (self, pjob),
                    pjob.seq * self.quantum - pjob.job.computation_time,
                    cpu=cpu_min, in_ms=True)
                timer.start()
                self.timers.append(timer)

                return (pjob.job, cpu_min)
        elif self.pseudo_job[cpu] is None:
            return (None, cpu)
