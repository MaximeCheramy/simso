# coding=utf-8

from simso.core.etm.AbstractExecutionTimeModel \
    import AbstractExecutionTimeModel


def calc_cpi(base_cpi, mix, miss_rates, penalties):
    """
    Compute the CPI using the miss_rates and penalties.
    """
    penalty_per_memaccess = penalties[0]
    for mp, mr in zip(penalties[1:], miss_rates):
        penalty_per_memaccess += mp * mr
    return base_cpi + mix * penalty_per_memaccess


def capacity_miss_LRU(csdp, cache_size):
    """
    Capacity miss rate using an LRU cache.
    """
    return 1.0 - csdp.get(int(cache_size + .5))


def cpi_alone(task, cache_sizes, penalties):
    miss_rates = [capacity_miss_LRU(task.csdp, cache_size)
                  for cache_size in cache_sizes]
    return calc_cpi(task.base_cpi, task.mix, miss_rates, penalties)


def calc_cache_sizes(caches, task, running_jobs):
    """
    Compute the virtual size of the cache taking into account the other running
    tasks (FOA model).
    """
    result = []
    for cache in caches:
        shared_jobs = [j for j in running_jobs if j.cpu in cache.shared_with]
        sum_af = sum(j.task.mix / j.task.get_cpi_alone() for j in shared_jobs)
        proportion = (task.mix / task.get_cpi_alone()) / sum_af

        result.append(cache.size * proportion)
    return result


def compute_instructions(task, running_jobs, duration):
    caches = task.cpu.caches
    penalties = [task.cpu.penalty_memaccess] + [c.penalty for c in caches]
    sizes = calc_cache_sizes(caches, task, running_jobs)
    miss_rates = [capacity_miss_LRU(task.csdp, size) for size in sizes]
    return duration / calc_cpi(task.base_cpi, task.mix, miss_rates, penalties)


class CacheModel(AbstractExecutionTimeModel):
    def __init__(self, sim, nb_processors):
        self.sim = sim
        self._nb_processors = nb_processors

    def init(self):
        self._last_update = 0
        self._running_jobs = set()
        self._instr_jobs = {}
        self._total_preemptions_cost = 0
        self.running = {}
        self.penalty = {}
        self.was_running_on = {}

        # precompute cpi_alone for each task on each cpu
        for task in self.sim.task_list:
            for proc in self.sim.processors:
                caches = proc.caches
                task.set_cpi_alone(
                    proc,
                    cpi_alone(task, [c.size for c in caches],
                              [proc.penalty_memaccess] +
                              [c.penalty for c in caches])
                )

    def update(self):
        self._update_instructions()

    def _update_instructions(self):
        for job in self._running_jobs:
            # Compute number of instr for self.sim.now() - last_update
            instr = compute_instructions(job.task, self._running_jobs,
                                         self.sim.now() - self._last_update)
            # Update the number of instr for this job
            self._instr_jobs[job] = self._instr_jobs.get(job, 0) + instr

        # Update last_update
        self._last_update = self.sim.now()

    def on_activate(self, job):
        self.penalty[job] = 0

    def on_execute(self, job):
        # Compute penalty.
        if job in self.was_running_on:
            # resume on the same processor.
            if self.was_running_on[job] is job.cpu:
                if self.running[job.cpu] is not job:
                    self.penalty[job] += job.task.preemption_cost
            else:  # migration.
                self.penalty[job] += job.task.preemption_cost

        self.running[job.cpu] = job
        self.was_running_on[job] = job.cpu

        # Update the number of instructions executed for the running jobs.
        self._update_instructions()
        # Add the job in the list of running jobs.
        self._running_jobs.add(job)

    def _stop_job(self, job):
        # Update the number of instructions executed for the running jobs.
        self._update_instructions()
        # Remove the job from the list of running jobs.
        self._running_jobs.remove(job)

    def on_preempted(self, job):
        self._stop_job(job)

    def on_terminated(self, job):
        self._stop_job(job)

    def on_abort(self, job):
        self._stop_job(job)

    def get_ret(self, job):
        self._update_instructions()
        penalty = self.penalty[job]
        return (job.task.n_instr - self._instr_jobs[job]) \
            * job.task.get_cpi_alone() + penalty
