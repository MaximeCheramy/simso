from simso.core.ProcEvent import ProcEvent
from simso.core.JobEvent import JobEvent
from simso.core.SchedulerEvent import SchedulerEvent


class ProcessorR(object):
    """
    Add information about a processor such as the number of CxtSave and
    CxtLoad and their total overhead.
    """
    def __init__(self):
        self.context_save_overhead = 0
        self.context_save_count = 0
        self.context_load_overhead = 0
        self.context_load_count = 0


class SchedulerR(object):
    """
    Add information about the scheduler such as the number of scheduling
    events and their total overhead.
    """
    def __init__(self):
        self.schedule_overhead = 0
        self.activate_overhead = 0
        self.terminate_overhead = 0
        self.schedule_count = 0
        self.activate_count = 0
        self.terminate_count = 0


class TaskR(object):
    """
    Add a set of metrics to a task. These metrics include: task_migrations,
    abortion count, etc.

    The attribute jobs contains a list of JobR, sorted by activation date.
    """
    def __init__(self, task, delta_preemption=100):
        self.task = task
        self.delta_preemption = delta_preemption
        self.jobs = []
        self.waiting_jobs = []
        self.resumptions = []
        self.task_migrations = []
        self.abort_count = 0
        self.execute_date = None
        self.preempt_date = None
        self.cpu = None
        self.other_executed = False

    def add_job(self, date, job):
        jobr = JobR(date, job)
        self.jobs.append(jobr)
        self.waiting_jobs.append(jobr)
        if len(self.waiting_jobs) == 1:
            jobr.start(date)

    def terminate_job(self, date):
        if self.waiting_jobs:
            self.preempt(date)
            self.waiting_jobs[0].terminate(date)
            self.waiting_jobs.pop(0)
            if self.waiting_jobs:
                self.waiting_jobs[0].start(date)
            self.preempt_date = None

    def abort_job(self, date):
        if self.waiting_jobs:
            self.preempt(date)
            self.waiting_jobs[0].abort(date)
            self.waiting_jobs.pop(0)
            self.abort_count += 1
            if self.waiting_jobs:
                self.waiting_jobs[0].start(date)
            self.preempt_date = None

    def execute(self, date, cpu):
        if self.waiting_jobs:
            if self.waiting_jobs[0].computation_time == 0:
                if self.cpu == cpu or self.cpu is None:
                    self.resumptions.append((date, self.waiting_jobs[0]))
                else:
                    self.task_migrations.append((date, self.waiting_jobs[0]))
            else:
                if self.cpu == cpu:
                    self.waiting_jobs[0].preemption_count += 1
                    if date - self.preempt_date > self.delta_preemption:
                        self.waiting_jobs[0].preemption_delta_count += 1
                    if self.other_executed:
                        self.waiting_jobs[0].preemption_inter_count += 1
                else:
                    self.waiting_jobs[0].migration_count += 1
                    if date - self.preempt_date > self.delta_preemption:
                        self.waiting_jobs[0].migration_delta_count += 1

            self.execute_date = date
            self.cpu = cpu
        self.preempt_date = None

    def preempt(self, date):
        if (self.execute_date is not None
                and self.execute_date < date and self.waiting_jobs):
            self.waiting_jobs[0].add_exec_time(date - self.execute_date)
        self.execute_date = None
        self.preempt_date = date
        self.other_executed = False

    @property
    def resumption_count(self):
        return len(self.resumptions)

    @property
    def task_migration_count(self):
        return len(self.task_migrations)

    @property
    def exceeded_count(self):
        count = 0
        for job in self.jobs:
            if job.exceeded_deadline:
                count += 1
        return count

    @property
    def migration_count(self):
        return sum(job.migration_count for job in self.jobs)

    @property
    def preemption_count(self):
        return sum(job.preemption_count for job in self.jobs)

    @property
    def preemption_inter_count(self):
        return sum(job.preemption_inter_count for job in self.jobs)

    @property
    def name(self):
        return self.task.name


class JobR(object):
    """
    Add a set of metrics to a job. Such metrics include: preemption count,
    migration count, response time, etc.
    """
    def __init__(self, date, job):
        self.job = job
        self.preemption_count = 0
        self.preemption_delta_count = 0
        self.preemption_inter_count = 0
        self.migration_count = 0
        self.migration_delta_count = 0
        self.activation_date = date
        self.aborted = False
        self.computation_time = 0
        self.end_date = None
        self.response_time = None
        self.start_date = None
        self.absolute_deadline = job.absolute_deadline_cycles

    def terminate(self, date):
        self.end_date = date
        self.response_time = date - self.activation_date

    def abort(self, date):
        self.aborted = True
        self.end_date = date
        self.response_time = date - self.activation_date

    def add_exec_time(self, duration):
        self.computation_time += duration

    def start(self, date):
        self.start_date = date

    @property
    def name(self):
        return self.job.name

    @property
    def exceeded_deadline(self):
        return self.end_date and (self.end_date > self.absolute_deadline
                                  or self.aborted)

    @property
    def normalized_laxity(self):
        return ((self.job.task.deadline - float(self.response_time)
                 / self.job.sim.cycles_per_ms) / self.job.task.period)

    @property
    def task(self):
        return self.job.task


class Results(object):
    """
    This class embeds and analyzes all the results from the simulation.
    This allows to retrieve the usual metrics.

    The Results instance object contains the following attributes:
        - `tasks`: a dictionary of TaskR where the key is the original Task.
        - `scheduler`: a SchedulerR instance.
        - `processors`: a dictionary of ProcessorR where the key is the \
            original Processor.

    .
    """
    def __init__(self, model):
        self.model = model
        self.error = None
        self._observation_window = None

        self.tasks = {}
        self.scheduler = None
        self.processors = {}
        self.total_timers = 0
        self.timers = None

    def end(self):
        self._analyze()

    def tasks_event(self):
        """
        Generator of the tasks events sorted by their date.
        """
        monitors = {}
        indices = {}
        for task in self.model.task_list:
            monitors[task] = task.monitor
            indices[task] = 0

        while True:
            m = None
            for task in self.model.task_list:
                if indices[task] < len(monitors[task]):
                    evt = monitors[task][indices[task]]
                    if m is None or evt[1].id_ < m[0][1].id_:
                        m = (evt, task)
            if m is None:
                break
            indices[m[1]] += 1
            yield m

    def _generate_tasks(self):
        self.tasks = {}

        for task in self.model.task_list:
            self.tasks[task] = TaskR(task)

        for evt, task in self.tasks_event():
            if (evt[0] < self.observation_window[0] or
                    evt[0] > self.observation_window[1]):
                # The events that start before the observation window should
                # maybe be stored...
                continue
            if evt[1].event == JobEvent.ACTIVATE:
                self.tasks[task].add_job(evt[0], evt[1].job)
            elif evt[1].event == JobEvent.TERMINATED:
                self.tasks[task].terminate_job(evt[0])
            elif evt[1].event == JobEvent.ABORTED:
                self.tasks[task].abort_job(evt[0])
            elif evt[1].event == JobEvent.EXECUTE:
                self.tasks[task].execute(evt[0], evt[1].cpu)
                for rt in self.tasks.values():
                    if rt.preempt_date and evt[1].cpu == rt.cpu:
                        rt.other_executed = True
            elif evt[1].event == JobEvent.PREEMPTED:
                self.tasks[task].preempt(evt[0])

    def _generate_scheduler(self):
        self.scheduler = SchedulerR()
        last = self.observation_window[0]
        for t, evt in self.model.scheduler.monitor:
            if (t < self.observation_window[0] or
                    t > self.observation_window[1]):
                continue

            if evt.event == SchedulerEvent.BEGIN_SCHEDULE:
                self.scheduler.schedule_count += 1
            elif evt.event == SchedulerEvent.END_SCHEDULE:
                self.scheduler.schedule_overhead += t - last
            elif evt.event == SchedulerEvent.BEGIN_ACTIVATE:
                self.scheduler.activate_count += 1
            elif evt.event == SchedulerEvent.END_ACTIVATE:
                self.scheduler.activate_overhead += t - last
            elif evt.event == SchedulerEvent.BEGIN_TERMINATE:
                self.scheduler.terminate_count += 1
            elif evt.event == SchedulerEvent.END_TERMINATE:
                self.scheduler.terminate_overhead += t - last
            last = t

    def _generate_processors(self):
        self.processors = {}
        for proc in self.model.processors:
            proc_r = ProcessorR()
            self.processors[proc] = proc_r
            last = self.observation_window[0]
            for t, evt in proc.monitor:
                if (t < self.observation_window[0] or
                        t > self.observation_window[1]):
                    continue
                if evt.event == ProcEvent.OVERHEAD and evt.args == "CS":
                    if evt.terminated:
                        proc_r.context_save_overhead += t - last
                    else:
                        proc_r.context_save_count += 1
                if evt.event == ProcEvent.OVERHEAD and evt.args == "CL":
                    if evt.terminated:
                        proc_r.context_load_overhead += t - last
                    else:
                        proc_r.context_load_count += 1
                last = t

    def _compute_timers(self):
        self.total_timers = 0
        self.timers = {}
        for proc in self.model.processors:
            self.timers[proc] = 0
            for t, evt in proc.timer_monitor:
                if (t < self.observation_window[0] or
                        t > self.observation_window[1]):
                    continue
                self.total_timers += 1
                self.timers[proc] += 1

    def _analyze(self):
        self._generate_tasks()
        self._generate_scheduler()
        self._generate_processors()
        self._compute_timers()

    def get_observation_window(self):
        """
        Get the observation window.
        """
        if self._observation_window is None:
            self._observation_window = (0, self.model.now())
        return self._observation_window

    def set_observation_window(self, window):
        """
        Set the observation window. The events that occurs outside of the
        observation window are discarded.
        """
        self._observation_window = window
        self._analyze()

    observation_window = property(get_observation_window,
                                  set_observation_window)

    @property
    def observation_window_duration(self):
        return self.observation_window[1] - self.observation_window[0]

    @property
    def total_migrations(self):
        migrations = 0
        for task in self.tasks.values():
            migrations += task.migration_count
        return migrations

    @property
    def total_preemptions(self):
        preemptions = 0
        for task in self.tasks.values():
            preemptions += task.preemption_count
        return preemptions

    @property
    def total_task_migrations(self):
        migrations = 0
        for task in self.tasks.values():
            migrations += task.task_migration_count
        return migrations

    @property
    def total_task_resumptions(self):
        resumptions = 0
        for task in self.tasks.values():
            resumptions += task.resumption_count
        return resumptions

    @property
    def total_exceeded_count(self):
        count = 0
        for task in self.tasks.values():
            count += task.exceeded_count
        return count

    def calc_load(self):
        """
        Yield a tuple (proc, load, overhead) for each processor.
        """
        for proc in self.model.processors:
            sum_run = 0
            sum_overhead = 0
            last_event = ProcEvent.IDLE
            x1 = self.observation_window[0]
            for evt in proc.monitor:
                current_date = evt[0]
                if current_date < self.observation_window[0]:
                    last_event = evt[1].event
                    continue
                if current_date >= self.observation_window[1]:
                    break

                if last_event == ProcEvent.RUN:
                    sum_run += current_date - x1
                elif last_event == ProcEvent.OVERHEAD:
                    sum_overhead += current_date - x1

                x1 = current_date
                last_event = evt[1].event

            if last_event == ProcEvent.RUN:
                sum_run += self.observation_window[1] - x1
            elif last_event == ProcEvent.OVERHEAD:
                sum_overhead += self.observation_window[1] - x1

            yield (proc,
                   float(sum_run) / self.observation_window_duration,
                   float(sum_overhead) / self.observation_window_duration)
