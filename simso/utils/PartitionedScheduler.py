from simso.core import Scheduler


def best_fit(scheduler, task_list=None):
    """
    Best-Fit heuristic. Put the tasks somewhere it fits but with the least
    spare place.
    """
    cpus = [[cpu, 0] for cpu in scheduler.processors]

    if task_list is None:
        task_list = scheduler.task_list

    for task in task_list:
        j = 0
        # Find a processor with free space.
        while cpus[j][1] * task.period + float(task.wcet) > task.period:
            j += 1
            if j >= len(scheduler.processors):
                print("oops bin packing failed.")
                return False

        # Affect it to the task.
        scheduler.affect_task_to_processor(task, cpus[j][0])

        # Update utilization.
        cpus[j][1] += float(task.wcet) / task.period

        cpus[:] = sorted(cpus, key=lambda c: -c[1])

    return True


def worst_fit(scheduler, task_list=None):
    """
    Worst-Fit heuristic. Put the tasks somewhere it fits with the largest
    spare place.
    """

    cpus = [[cpu, 0] for cpu in scheduler.processors]

    if task_list is None:
        task_list = scheduler.task_list

    for task in task_list:
        j = 0
        # Find a processor with free space.
        while cpus[j][1] * task.period + float(task.wcet) > task.period:
            j += 1
            if j >= len(scheduler.processors):
                print("oops bin packing failed.")
                return False

        # Affect it to the task.
        scheduler.affect_task_to_processor(task, cpus[j][0])

        # Update utilization.
        cpus[j][1] += float(task.wcet) / task.period

        cpus[:] = sorted(cpus, key=lambda c: c[1])

    return True


def next_fit(scheduler, task_list=None):
    """
    Next-Fit heuristic. Put each task on the next processor with enough space.
    """

    cpus = [[cpu, 0] for cpu in scheduler.processors]

    if task_list is None:
        task_list = scheduler.task_list

    j = 0
    for task in task_list:
        k = 0
        # Find a processor with free space.
        while cpus[j][1] * task.period + float(task.wcet) > task.period:
            j = (j + 1) % len(scheduler.processors)
            k += 1
            if k >= len(scheduler.processors):
                print("oops bin packing failed.")
                return False

        # Affect it to the task.
        scheduler.affect_task_to_processor(task, cpus[j][0])

        # Update utilization.
        cpus[j][1] += float(task.wcet) / task.period

    return True


def first_fit(scheduler, task_list=None):
    """
    First-Fit heuristic. Put each task on the first processor with enough
    space.
    """

    cpus = [[cpu, 0] for cpu in scheduler.processors]

    if task_list is None:
        task_list = scheduler.task_list

    for task in task_list:
        j = 0
        # Find a processor with free space.
        while cpus[j][1] * task.period + float(task.wcet) > task.period:
            j += 1
            if j >= len(scheduler.processors):
                print("oops bin packing failed.")
                return False

        # Affect it to the task.
        scheduler.affect_task_to_processor(task, cpus[j][0])

        # Update utilization.
        cpus[j][1] += float(task.wcet) / task.period

    return True


def decreasing_first_fit(scheduler):
    """
    First-Fit with tasks inversely sorted by their u_i.
    """
    return first_fit(
        scheduler, sorted(scheduler.task_list,
                          key=lambda t: -float(t.wcet) / t.period))


def decreasing_next_fit(scheduler):
    """
    Next-Fit with tasks inversely sorted by their u_i.
    """

    return next_fit(
        scheduler, sorted(scheduler.task_list,
                          key=lambda t: -float(t.wcet) / t.period))


def decreasing_best_fit(scheduler):
    """
    Best-Fit with tasks inversely sorted by their u_i.
    """

    return next_fit(
        scheduler, sorted(scheduler.task_list,
                          key=lambda t: -float(t.wcet) / t.period))


def decreasing_worst_fit(scheduler):
    """
    Worst-Fit with tasks inversely sorted by their u_i.
    """

    return next_fit(
        scheduler, sorted(scheduler.task_list,
                          key=lambda t: -float(t.wcet) / t.period))


class PartitionedScheduler(Scheduler):
    """
    The PartitionedScheduler class provide facilities to create a new
    Partitioned Scheduler. Only the packing phase is not done and should
    be overriden.
    """
    def init(self, scheduler_info, packer=None):
        """
        Args:
            - `scheduler_info`: A :class:`SchedulerInfo \
            <simso.core.Scheduler.SchedulerInfo>` object. One scheduler from \
            this SchedulerInfo will be instantiated for each processor.
        """
        assert scheduler_info is not None, \
            "PartitionedScheduler requires a monoprocessor scheduler to " \
            "instantiate."

        # Mapping processor to scheduler.
        self.map_cpu_sched = {}
        # Mapping task to scheduler.
        self.map_task_sched = {}

        for cpu in self.processors:
            # Instantiate a scheduler.
            sched = scheduler_info.instantiate(self.sim)
            sched.add_processor(cpu)

            # Affect the scheduler to the processor.
            self.map_cpu_sched[cpu.identifier] = sched

        self._packer = packer
        assert self.packer(), "Packing failed"

        for cpu in self.processors:
            self.map_cpu_sched[cpu.identifier].init()

    def packer(self):
        if self._packer:
            return self._packer(self)
        raise Exception("A bin packing method is required.")

    def affect_task_to_processor(self, task, proc):
        # Get the scheduler for this processor.
        sched = self.map_cpu_sched[proc.identifier]
        self.map_task_sched[task.identifier] = sched
        sched.add_task(task)
        # Put the task on that processor.
        task.cpu = proc

    def get_lock(self):
        # No lock mechanism is needed.
        return True

    def schedule(self, cpu):
        return self.map_cpu_sched[cpu.identifier].schedule(cpu)

    def on_activate(self, job):
        self.map_task_sched[job.task.identifier].on_activate(job)

    def on_terminated(self, job):
        self.map_task_sched[job.task.identifier].on_terminated(job)
