from simso.core.etm.AbstractExecutionTimeModel \
    import AbstractExecutionTimeModel


class FixedPenalty(AbstractExecutionTimeModel):
    def __init__(self, sim, _):
        self.sim = sim
        self.running = {}
        self.penalty = {}
        self.was_running_on = {}
        self.executed = {}
        self.on_execute_date = {}

    def init(self):
        pass

    def update_executed(self, job):
        if job in self.on_execute_date:
            self.executed[job] += (self.sim.now() - self.on_execute_date[job]
                                   ) * job.cpu.speed

            del self.on_execute_date[job]

    def on_activate(self, job):
        self.penalty[job] = 0
        self.executed[job] = 0

    def on_execute(self, job):
        self.on_execute_date[job] = self.sim.now()
        if job in self.was_running_on:
            # resume on the same processor.
            if self.was_running_on[job] is job.cpu:
                if self.running[job.cpu] is not job:
                    self.penalty[job] += self.sim.penalty_preemption
            else:  # migration.
                self.penalty[job] += self.sim.penalty_migration

        self.running[job.cpu] = job
        self.was_running_on[job] = job.cpu

    def on_preempted(self, job):
        self.executed[job] += (self.sim.now() - self.on_execute_date[job]
                               ) * job.cpu.speed

    def on_terminated(self, job):
        if job in self.on_execute_date:
            del self.on_execute_date[job]

    def on_abort(self, job):
        if job in self.on_execute_date:
            del self.on_execute_date[job]

    def get_executed(self, job):
        if job in self.on_execute_date:
            c = (self.sim.now() - self.on_execute_date[job]) * job.cpu.speed
        else:
            c = 0
        return self.executed[job] + c

    def get_ret(self, job):
        wcet_cycles = int(job.wcet * self.sim.cycles_per_ms)
        penalty = self.penalty[job]
        return int(wcet_cycles + penalty - job.computation_time_cycles)

    def update(self):
        for job in list(self.on_execute_date.keys()):
            self.update_executed(job)
