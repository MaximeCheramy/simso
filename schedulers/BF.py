"""
Implementation of the BF algorithm.
"""
from simso.core import Scheduler, Timer


class BF(Scheduler):
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

    def alpha_plus_one(self, job):
        deadlines = sorted([x.job.absolute_deadline for x in self.task_list])
        bk2 = deadlines[1]
        bk1 = deadlines[0]
        ui = job.wcet / job.deadline
        val = bk2 * ui - int(bk1 * ui) - bk2 + bk1
        if val == 0:
            return 0
        if val > 0:
            return 1
        return -1

    def uf_plus_one(self, job):
        bk1 = min([x.job.absolute_deadline for x in self.task_list])
        ui = job.wcet / job.deadline
        return (1. - (bk1 * ui - int(bk1 * ui))) / ui

    def nuf_plus_one(self, job):
        bk1 = min([x.job.absolute_deadline for x in self.task_list])
        ui = 1 - (job.wcet / job.deadline)
        return (1. - (bk1 * ui - int(bk1 * ui))) / ui

    def compare(self, job_i, job_j):
        ai = self.alpha_plus_one(job_i)
        aj = self.alpha_plus_one(job_j)
        if ai > aj:
            return -1
        elif ai < aj:
            return 1
        elif ai == 0:
            return -1
        elif ai == -1:
            if self.uf_plus_one(job_i) > self.uf_plus_one(job_j):
                return 1
            else:
                return -1
        else:
            if self.nuf_plus_one(job_i) >= self.nuf_plus_one(job_j):
                return -1
            else:
                return 1

    def init_interval(self):
        """
        Determine the end of the interval and compute allocation of the jobs
        to the processors using the McNaughton algorithm.
        """
        self.allocations = [[0, []] for _ in self.processors]
        self.t_f = int(min([x.job.absolute_deadline for x in self.task_list])
                       * self.sim.cycles_per_ms)
        # Duration that can be allocated for each processor.
        w = int(self.t_f - self.sim.now())
        p = 0  # Processor id.
        mand = {}
        available = w * len(self.processors)
        eligible = []

        for task in self.task_list:
            job = task.job
            if not job.is_active():
                continue

            fluid = (self.sim.now() - job.activation_date *
                     self.sim.cycles_per_ms) * job.wcet / job.period
            lag = fluid - job.computation_time_cycles
            mand[task.identifier] = max(0,
                                        int(lag + w * job.wcet / job.period))
            available -= mand[task.identifier]
            if mand[task.identifier] < w:
                eligible.append(task)

        while available > 0 and eligible:
            job_m = None
            for task in eligible:
                if job_m is None or self.compare(task.job, job_m) == -1:
                    job_m = task.job
            mand[job_m.task.identifier] += 1
            eligible.remove(job_m.task)
            available -= 1

        for task in self.task_list:
            # The "fair" duration for this job on that interval. Rounded to the
            # upper integer to avoid durations that are not multiples of
            # cycles.
            job = task.job
            if not job.is_active():
                continue
            duration = mand[task.identifier]
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
                timer = Timer(self.sim, BF.end_event,
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
