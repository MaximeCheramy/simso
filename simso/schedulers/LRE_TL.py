"""
Implementation of the LRE-TL scheduler as presented by S. Funk in "LRE-TL: An
Optimal Multiprocessor Scheduling Algorithm for Sporadic Task Sets".
"""

from simso.core import Scheduler, Timer
from heapq import heappush, heapreplace, heappop, heapify
from math import ceil
from simso.schedulers import scheduler

@scheduler("simso.schedulers.LRE_TL")
class LRE_TL(Scheduler):
    def init(self):
        """
        Initialization of the scheduler. This function is called when the
        system is ready to run.
        """
        self.t_f = 0
        self.h_b = []  # Heap of running tasks.
        self.h_c = []  # Heap of waiting tasks.
        self.h_d = []  # Heap of deadlines.
        self.pmin = min([task.period for task in self.task_list]) \
            * self.sim.cycles_per_ms
        self.evt_bc = False
        self.activations = []
        self.waiting_schedule = False

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
        A-event.
        """
        self.activations.append(job.task)
        self.reschedule()

    def init_tl_plane(self):
        decisions = []

        for task in self.activations:
            dl = int(task.job.absolute_deadline * self.sim.cycles_per_ms)
            if dl not in self.h_d:
                heappush(self.h_d, dl)

        self.t_f = self.sim.now() + self.pmin
        if self.h_d[0] <= self.t_f:
            self.t_f = heappop(self.h_d)

        z = 0
        self.h_b = []
        self.h_c = []
        for task in self.task_list:
            l = ceil(task.wcet * (self.t_f - self.sim.now()) / task.period)
            if z < len(self.processors) and task.job.is_active():
                heappush(self.h_b, (self.sim.now() + l, task))
                decisions.append((task.job, self.processors[z]))
                z += 1
            else:
                heappush(self.h_c, (self.t_f - l, task))

        while z < len(self.processors):
            decisions.append((None, self.processors[z]))
            z += 1

        return decisions

    def handle_evt_a(self, task):
        """
        Handle an "A-Event".
        """
        decisions = []

        tasks_h_c = [t for _, t in self.h_c]
        tasks_h_b = [t for _, t in self.h_b]

        if task not in tasks_h_b and task not in tasks_h_c:
            l = ceil(task.wcet * (self.t_f - self.sim.now()) / task.period)
            if len(self.h_b) < len(self.processors):
                idle_proc = [z for z in self.processors
                             if not z.is_running()][0]
                decisions.append((task.job, idle_proc))
                heappush(self.h_b, (self.sim.now() + l, task))
            else:
                if task.wcet < task.period:
                    heappush(self.h_c, ((self.t_f - l), task))
                else:
                    key_b, task_b = heapreplace(self.h_b, (self.t_f + l, task))
                    heappush(self.h_c, (self.t_f - key_b + self.sim.now()))

        dl = int(task.job.absolute_deadline * self.sim.cycles_per_ms)
        if dl not in self.h_d:
            heappush(self.h_d, dl)

        return decisions

    def handle_evt_bc(self):
        """
        Handle a "BC-Event".
        """

        decisions = []
        while self.h_b and self.h_b[0][0] == self.sim.now():
            task_b = heappop(self.h_b)[1]

            if self.h_c:
                key_c, task_c = heappop(self.h_c)
                heappush(self.h_b, (self.t_f - key_c + self.sim.now(), task_c))
                decisions.append((task_c.job, task_b.cpu))
            else:
                decisions.append((None, task_b.cpu))

        if self.h_c:
            while self.h_c[0][0] == self.sim.now():
                key_b, task_b = heappop(self.h_b)
                key_c, task_c = heappop(self.h_c)
                key_b = self.t_f - key_b + self.sim.now()
                assert key_c != key_b, "Handle Evt BC failed."
                key_c = self.t_f - key_c + self.sim.now()
                heappush(self.h_b, (key_c, task_c))
                heappush(self.h_c, (key_b, task_b))
                decisions.append((task_c.job, task_b.cpu))

        return decisions

    def event_bc(self):
        """
        B or C event.
        """
        self.evt_bc = True
        self.reschedule()

    def schedule(self, cpu):
        """
        Take the scheduling decisions.
        """
        self.waiting_schedule = False
        decisions = []
        self.h_c = [(d, t) for d, t in self.h_c if t.job.is_active()]
        heapify(self.h_c)

        if self.sim.now() == self.t_f:
            decisions = self.init_tl_plane()
        else:
            for task in self.activations:
                decisions += self.handle_evt_a(task)
            if self.evt_bc:
                decisions += self.handle_evt_bc()

        self.activations = []
        self.evt_bc = False

        if self.h_b:
            t_next = self.h_b[0][0]
            if self.h_c:
                t_next = min(t_next, self.h_c[0][0])

            self.timer = Timer(self.sim, LRE_TL.event_bc, (self,),
                               t_next - self.sim.now(),
                               cpu=self.processors[0], in_ms=False)
        else:
            self.timer = Timer(self.sim, LRE_TL.reschedule, (self,),
                               self.t_f - self.sim.now(),
                               cpu=self.processors[0], in_ms=False)
        self.timer.start()

        return decisions
