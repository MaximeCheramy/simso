"""
Implementation of the LLREF scheduler as presented by Cho et al. in
"An Optimal Real-Time Scheduling Algorithm for Multiprocessors".
"""

from simso.core import Scheduler, Timer
from math import ceil
from simso.schedulers import scheduler

@scheduler("simso.schedulers.LLREF")
class LLREF(Scheduler):
    def init(self):
        self.selected_jobs = []  # Jobs currently running.
        self.budget = {}  # Budgets for the active jobs.
        self.next_deadline = 0
        self.waiting_schedule = False
        self.last_update = 0  # Used to update the budget.

    def reschedule(self, cpu=None):
        """
        Ask for a scheduling decision. Don't call if not necessary.
        """
        if not self.waiting_schedule:
            if cpu is None:
                cpu = self.processors[0]
            cpu.resched()
            self.waiting_schedule = True

    def on_activate(self, job):
        """
        Deal with a job activation. The budget for this job is computed.
        """
        # Compute budget for this newly activated job
        window = self.next_deadline - self.sim.now()
        self.budget[job] = window * job.wcet / job.period

        # Find the next absolute deadline among the ready jobs.
        m_dl = min([rjob.absolute_deadline for rjob in self.budget.keys()]) \
            * self.sim.cycles_per_ms

        # Refill the budgets if we change the interval
        if m_dl != self.next_deadline:
            window = m_dl - self.next_deadline
            self.next_deadline = m_dl
            for j in self.budget.keys():
                self.budget[j] += window * j.wcet / j.period

        # There's a new job, the system should be rescheduled.
        self.reschedule()

    def on_terminated(self, job):
        if job in self.budget:
            del self.budget[job]

    def update_budget(self):
        """
        Remove budget from the currently executing jobs.
        """
        time_since_last_update = self.sim.now() - self.last_update
        for job in self.selected_jobs:
            if job in self.budget:
                if job.is_active():
                    self.budget[job] -= time_since_last_update
                else:
                    del self.budget[job]
        self.last_update = self.sim.now()

    def date_next_event(self, selected, not_selected):
        next_event = 0

        if selected:
            next_bottom_hitting = selected[-1][1]
            next_event = next_bottom_hitting

        if not_selected:
            next_ceiling_hitting = self.next_deadline - self.sim.now() \
                - not_selected[0][1]
            if next_ceiling_hitting < next_bottom_hitting:
                next_event = next_ceiling_hitting

        return next_event

    def schedule(self, cpu):
        self.waiting_schedule = False
        self.update_budget()

        # Sort the jobs by budgets.
        sorted_budgets = sorted(
            [(x, ceil(y)) for x, y in self.budget.items()],
            key=lambda x: (-x[1], x[0].name))
        selected = sorted_budgets[:len(self.processors)]
        not_selected = sorted_budgets[len(self.processors):]

        # Compute the (relative) date of the next event.
        next_event = self.date_next_event(selected, not_selected)
        if next_event > 0:
            # Set a timer to reschedule the system at that date.
            self.timer_a = Timer(self.sim, LLREF.reschedule, (self,),
                                 next_event, cpu=cpu, in_ms=False)
            self.timer_a.start()

        # Allocate the selected jobs to the processors.
        # The processors already running selected jobs are not changed.
        available_procs = []
        self.selected_jobs = [s[0] for s in selected if s[1] > 0]
        remaining_jobs = self.selected_jobs[:]
        for proc in self.processors:
            if proc.running in self.selected_jobs:
                # This processor keeps running the same job.
                remaining_jobs.remove(proc.running)
            else:
                # This processor is not running a selected job.
                available_procs.append(proc)

        # The remaining processors are running the remaining jobs or None.
        padded_remaining_jobs = remaining_jobs + \
            [None] * (len(available_procs) - len(remaining_jobs))
        # zip create a list of couples (job, proc) using the list of remaining
        # jobs and the list of available processors.
        decisions = list(zip(padded_remaining_jobs, available_procs))

        return decisions
