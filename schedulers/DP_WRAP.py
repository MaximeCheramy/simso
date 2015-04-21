"""
Implementation of the DP-WRAP algorithm as presented by Levin et al. in
"DP-FAIR: A Simple Model for Understanding Optimal Multiprocessor Scheduling".
"""
from simso.core import Scheduler, Timer
from math import ceil


class DP_WRAP(Scheduler):
    def init(self):
        self.t_f = 0
        self.waiting_schedule = False
        self.mirroring = False
        self.allocations = []
        self.timers = {}

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
        self.reschedule()

    def init_interval(self):
        """
        Determine the end of the interval and compute allocation of the jobs
        to the processors using the McNaughton algorithm.
        """
        self.allocations = [[0, []] for _ in self.processors]
        self.t_f = ceil(min([x.job.absolute_deadline for x in self.task_list]
                            ) * self.sim.cycles_per_ms)
        # Duration that can be allocated for each processor.
        w = int(self.t_f - self.sim.now())
        p = 0  # Processor id.
        for task in self.task_list:
            job = task.job
            if not job.is_active():
                continue
            # The "fair" duration for this job on that interval. Rounded to the
            # upper integer to avoid durations that are not multiples of
            # cycles.
            duration = ceil(w * job.wcet / job.period)
            if self.allocations[p][0] + duration <= w:
                self.allocations[p][1].append((job, duration))
                self.allocations[p][0] += duration
            else:
                # Add first part to the end of the current processor p:
                duration1 = w - self.allocations[p][0]
                if duration1 > 0:
                    self.allocations[p][1].append((job, duration1))
                    self.allocations[p][0] = w

                if p + 1 < len(self.processors):
                    # Add the second part:
                    duration2 = duration - duration1
                    self.allocations[p + 1][1].append((job, duration2))
                    self.allocations[p + 1][0] += duration2
                else:
                    # Because every durations are rounded to the upper value,
                    # the last job may have not enough space left.
                    # This could probably be improved.
                    print("Warning: didn't allowed enough time to last task.",
                          duration - duration1)
                    break

                p += 1

        for allocation in self.allocations:
            if allocation[0] < w:
                allocation[1].append((None, w - allocation[0]))

        if self.mirroring:
            for allocation in self.allocations:
                # Rerverse the order of the jobs.
                # Note: swapping the first and last items should be enough.
                allocation[1].reverse()
        self.mirroring = not self.mirroring

    def end_event(self, z, job):
        """
        Called when a job's budget has expired.
        """
        del self.timers[job]
        l = self.allocations[z][1]
        if l and l[0][0] is job:
            l.pop(0)
        self.reschedule(self.processors[z])

    def schedule(self, cpu):
        """
        Schedule main method.
        """
        self.waiting_schedule = False
        # At the end of the interval:
        if self.sim.now() >= self.t_f:
            self.init_interval()

            # Stop current timers.
            for job, timer in self.timers.items():
                timer.stop()
            self.timers = {}

        # Set timers to stop the jobs that will run.
        for z, proc in enumerate(self.processors):
            l = self.allocations[z][1]
            if l and l[0][0] not in self.timers:
                timer = Timer(self.sim, DP_WRAP.end_event,
                              (self, z, l[0][0]), l[0][1],
                              cpu=proc, in_ms=False)
                timer.start()
                self.timers[l[0][0]] = timer

        # Schedule the activated tasks on each processor.
        decisions = []
        for z, proc in enumerate(self.processors):
            l = self.allocations[z][1]
            if not l[0][0] or l[0][0].is_active():
                decisions.append((l[0][0] if l else None, proc))

        return decisions
