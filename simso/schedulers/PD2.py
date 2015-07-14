# coding=utf-8

from simso.core import Scheduler, Timer
from math import ceil
from simso.schedulers import scheduler


def rounded_wcet(job, q=None):
    return rounded_wcet_cycles(job, q) / job.sim.cycles_per_ms


def rounded_wcet_cycles(job, q=None):
    if q is None:
        q = PD2.quantum
    wcet_cycles = job.wcet * job.sim.cycles_per_ms
    if wcet_cycles % q:
        return wcet_cycles + q - (wcet_cycles % q)
    else:
        return wcet_cycles


class VirtualJob(object):
    """
    A Virtual Job contains the list of the pseudo jobs for an actual job.
    """
    def __init__(self, job):
        self.job = job
        self.pseudo_jobs = []
        self.cur = 0
        seq = 0

        # Create pseudo jobs:
        while seq * PD2.quantum <= job.wcet * job.sim.cycles_per_ms:
            self.pseudo_jobs.append(PseudoJob(job, seq + 1))
            seq += 1

    def get_next_job(self):
        if self.cur < len(self.pseudo_jobs) - 1:
            self.cur += 1
            job = self.pseudo_jobs[self.cur]
            return job

    def get_current_job(self):
        if self.cur < len(self.pseudo_jobs):
            return self.pseudo_jobs[self.cur]


class PseudoJob(object):
    def __init__(self, job, seq):
        self.job = job
        self.release_date = int(job.deadline * (seq - 1) / rounded_wcet(job)
                                ) * PD2.quantum
        self.deadline = int(ceil(job.deadline * seq / rounded_wcet(job))
                            ) * PD2.quantum
        self.seq = seq
        self.succ_bit = PseudoJob.succ_bit(job, seq)
        if rounded_wcet(job) / job.deadline < 0.5:
            self.group_deadline = 0
        else:
            j = seq + 1
            while (j * PD2.quantum <= rounded_wcet_cycles(job) and
                    PseudoJob.succ_bit(job, j - 1) == 1 and
                    PseudoJob.win_size(job, j) == 2):
                # while the window size is 2 and succ_bit of the prev is 1
                j += 1
            self.group_deadline = int(ceil(
                job.deadline * (j - 1) / rounded_wcet(job)
                * job.sim.cycles_per_ms))

    @property
    def absolute_releasedate(self):
        return self.release_date + \
            self.job.activation_date * self.job.sim.cycles_per_ms

    def cmp_key(self):
        # Si le premier parametre est identique, il regarde le second, etc.
        cycles_per_ms = self.job.sim.cycles_per_ms
        return (self.deadline + self.job.activation_date * cycles_per_ms,
                -self.succ_bit,
                -(self.job.activation_date + self.group_deadline))

    @staticmethod
    def succ_bit(job, seq):
        return int(ceil(seq * job.deadline / rounded_wcet(job))) \
            - int(seq * job.deadline / rounded_wcet(job))

    @staticmethod
    def win_size(job, seq):
        return int(ceil(seq * job.deadline / rounded_wcet(job))) \
            - int((seq - 1) * job.deadline / rounded_wcet(job))

@scheduler("simso.schedulers.PD2")
class PD2(Scheduler):
    quantum = 100000  # cycles

    def init(self):
        self.ready_list = []
        self.timers = []
        self.terminate_timers = []
        self.waiting_schedule = False
        self.running_vjobs = []

        # PD2.quantum = 1000000
        # while not self.is_schedulable() and PD2.quantum > 1000:
        #     PD2.quantum /= 2
            
        PD2.quantum = self.sim.cycles_per_ms // 10

        self.timer = Timer(
            self.sim, PD2.reschedule, (self, ), PD2.quantum,
            cpu=self.processors[0], in_ms=False, one_shot=False)
        self.timer.start()

    def is_schedulable(self, q=None):
        load = 0.0
        cycles_per_ms = self.sim.cycles_per_ms
        for task in self.task_list:
            wcet = rounded_wcet_cycles(task, q)
            load += wcet / task.period
            if wcet > task.period * cycles_per_ms \
                    or load > len(self.processors) * cycles_per_ms:
                return False
        return True

    def reschedule(self, cpu=None):
        """
        Ask for a scheduling decision. Don't call if not necessary.
        """
        if not self.waiting_schedule:
            if cpu is None:
                cpu = self.processors[0]
            cpu.resched()
            self.waiting_schedule = True

    def virtual_terminate(self, virtual_job):
        pjob = virtual_job.get_next_job()
        if not pjob or not virtual_job.job.is_active():
            self.ready_list.remove(virtual_job)

    def on_activate(self, job):
        virtual_job = VirtualJob(job)
        self.ready_list.append(virtual_job)

        if self.sim.now() == 0:
            self.reschedule()

    def schedule(self, cpu):
        self.waiting_schedule = False

        decisions = []

        for vjob in self.running_vjobs:
            self.virtual_terminate(vjob)

        vjobs = [vjob for vjob in self.ready_list if vjob.job.is_active() and
                 self.sim.now() >= vjob.get_current_job().absolute_releasedate]

        self.running_vjobs = sorted(
            vjobs,
            key=lambda x: x.get_current_job().cmp_key()
        )[:len(self.processors)]

        selected_jobs = [vjob.job for vjob in self.running_vjobs]
        remaining_jobs = selected_jobs[:]
        available_procs = []

        # Remove from the list of remaining jobs the jobs that already runs.
        for proc in self.processors:
            if proc.running in selected_jobs:
                # This processor keeps running the same job.
                remaining_jobs.remove(proc.running)
            else:
                # This processor is not running a selected job.
                available_procs.append(proc)

        # Jobs not currently running
        for vjob in self.running_vjobs:
            if vjob.job in remaining_jobs:
                decisions.append((vjob.job, available_procs.pop()))

        # Unused processors
        for proc in available_procs:
            decisions.append((None, proc))

        return decisions
