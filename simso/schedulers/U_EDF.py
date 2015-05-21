"""
Implementation of the U-EDF scheduler as presented by Nelissen et al. in
"U-EDF an unfair but optimal multiprocessor scheduling algorithm for sporadic
tasks"
"""


from simso.core import Scheduler, Timer
from math import ceil


class U_EDF(Scheduler):
    def init(self):
        self.al = {}
        self.timer = None
        self.toresched = False
        self.running_jobs = {}
        self.last_event = 0
        self.newly_activated = False

        self.ui = {task: task.wcet / task.period for task in self.task_list}

    def reschedule(self):
        if not self.toresched:
            self.processors[0].resched()
        self.toresched = True

    def hp(self, job):
        for task in self.sorted_task_list:
            if task.job is job:
                return
            else:
                yield task.job

    def res(self, job, j, t1, t2):
        s = self.s[job]
        u = max(0, min(1, (s + self.ui[job.task] - j)))\
            - max(0, min(1, (s - j)))
        return (t2 - t1) * u

    def bdg(self, job, j, t2):
        return self.al[job][j] + self.res(
            job, j, job.absolute_deadline * self.sim.cycles_per_ms, t2)

    def compute_al(self):
        t = self.sim.now()
        cycles_per_ms = self.sim.cycles_per_ms

        self.sorted_task_list = sorted(
            self.task_list,
            key=lambda t: (t.job.absolute_deadline, t.identifier))

        self.s = {}
        for task in self.task_list:
            self.al[task.job] = [0] * len(self.processors)
            self.s[task.job] = sum(self.ui[x.task] for x in self.hp(task.job))

        for task in self.sorted_task_list:
            job = task.job

            if not job.is_active():
                continue

            for j in range(len(self.processors)):
                almax = (job.absolute_deadline * cycles_per_ms - t) \
                    - sum(self.bdg(x, j, job.absolute_deadline * cycles_per_ms)
                          for x in self.hp(job)) - sum(self.al[job])
                self.al[job][j] = int(ceil(min(
                    almax, job.ret * self.sim.cycles_per_ms
                    - sum(self.al[job]))))

    def on_activate(self, job):
        self.newly_activated = True
        self.reschedule()

    def update_al(self):
        delta = self.sim.now() - self.last_event

        for job, j in self.running_jobs.items():
            self.al[job][j] -= delta

    def schedule(self, cpu):
        self.toresched = False

        if self.newly_activated:
            self.compute_al()
            self.newly_activated = False
        else:
            self.update_al()

        self.last_event = self.sim.now()

        next_event = None
        decisions = []
        selected_jobs = {}

        # Select the jobs:
        for j, proc in enumerate(self.processors):
            eligible = [task.job for task in self.task_list
                        if task.job.is_active()
                        and task.job not in selected_jobs
                        and task.job in self.al
                        and self.al[task.job][j] > 0]

            if not eligible:
                continue

            job = min(eligible,
                      key=lambda x: (x.absolute_deadline, x.task.identifier))
            if next_event is None or next_event > self.al[job][j]:
                next_event = self.al[job][j]
            selected_jobs[job] = j

        # Set the timer for the next event:
        if self.timer:
            self.timer.stop()
            self.timer = None
        if next_event is not None:
            self.timer = Timer(self.sim, U_EDF.reschedule, (self,),
                               next_event, self.processors[0], in_ms=False)
            self.timer.start()

        # Bind jobs to processors:
        jobs = list(selected_jobs.keys())
        available_procs = list(self.processors)
        was_not_running = []
        for job in jobs:
            if job in self.running_jobs:
                available_procs.remove(job.cpu)
            else:
                was_not_running.append(job)

        remaining_jobs = []
        for job in was_not_running:
            if job.cpu in available_procs:
                decisions.append((job, job.cpu))
                available_procs.remove(job.cpu)
            else:
                remaining_jobs.append(job)

        for p, job in enumerate(remaining_jobs):
            decisions.append((job, available_procs[p]))

        self.running_jobs = selected_jobs

        return decisions
