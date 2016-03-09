"""
Implementation of the SCHED_DEADLINE for LINUX multiprocessor

Juri Lelli, Claudio Scordino, Luca Abeni and Dario Faggioli. Deadline scheduling
in the Linux kernel. Softw. Pract. Exper. (2015) DOI: 10.1002/spe.2335
"""
from simso.core import Scheduler, Timer
from simso.schedulers import scheduler


@scheduler("simso.schedulers.SCHED_DEADLINE",
           required_task_fields=[
               {'name': 'cbs_period', 'type': 'float', 'default': '0.'},
               {'name': 'cbs_deadline', 'type': 'float', 'default': '0.'},
               {'name': 'cbs_maximum_runtime', 'float': 'int', 'default': '0.'}
           ]
           )
class SCHED_DEADLINE(Scheduler):
    """SCHED_DEADLINE"""

    def init(self):
        # Create a server for each task
        list_servers = [CBSServer(task, task.data['cbs_period'],
                                  task.data['cbs_maximum_runtime'],
                                  task.data['cbs_deadline'])
                        for task in self.task_list]
        self.cbs_servers = dict(zip(self.task_list, list_servers))

    def on_activate(self, job):

        server = self.cbs_servers[job.task]

        # If the ready list of the server is empty new runtime and deadline are computed and
        # the deadline_timer is started
        if (not server.ready_list):
            # qi < (di - t)Qi/Ti
            if not (server.current_runtime <
                            (server.current_deadline - self.sim.now_ms())
                            * (server.maximum_runtime / server.deadline)):
                # d = t + D, q = Q
                self.cbs_servers[job.task].set(self.cbs_servers[job.task].maximum_runtime,
                                               self.sim.now_ms() + self.cbs_servers[job.task].deadline,
                                               self.sim.now_ms(),
                                               Timer(self.sim, SCHED_DEADLINE.deadline_call,
                                                     (self, self.cbs_servers[job.task]),
                                                     self.cbs_servers[job.task].deadline, one_shot=True,
                                                     cpu=self.processors[0], overhead=.000))
        # The job is added to the ready_list of the server
        server.add_job(job)
        job.cpu.resched()

    def on_terminated(self, job):
        server = self.cbs_servers[job.task]
        # The job is removed from the ready_list of the server
        server.remove_job(job)
        job.cpu.resched()

    def schedule(self, cpu):
        # update runtime of the running server on cpu if exists
        if cpu.running:
            self.cbs_servers[cpu.running.task].update_runtime(self.sim.now_ms())

        # List of CBS servers with a ready job which is not currently running
        ready_servers = [s for s in self.cbs_servers.values()
                         if s.ready_list and not s.ready_list[0].is_running()
                         and not s.is_throttled]

        # Choose the job-server and processor with EDF citeria
        if ready_servers:
            # Select a free processor or, if none,
            # the one with the greatest server-deadline (self in case of equality):
            key = lambda x: (
                1 if not x.running else 0,
                self.cbs_servers[x.running.task].current_deadline if x.running else 0,
                1 if x is cpu else 0
            )
            cpu_min = max(self.processors, key=key)

            # Select the job with the least server-deadline
            server = min(ready_servers, key=lambda x: x.current_deadline)
            job = server.ready_list[0]

            if (cpu_min.running is None or
                        self.cbs_servers[cpu_min.running.task].current_deadline > self.cbs_servers[
                        job.task].current_deadline):
                print(self.sim.now(), job.name, cpu_min.name)

                # start runtime timer of the new server selected
                self.cbs_servers[job.task].timer_runtime = Timer(self.sim, SCHED_DEADLINE.runtime_call,
                      (self, self.cbs_servers[job.task]), self.cbs_servers[job.task].current_runtime, one_shot=True,
                      cpu=self.processors[0], overhead=.000)
                self.cbs_servers[job.task].timer_runtime.start()
                self.cbs_servers[job.task].last_update = self.sim.now_ms()
                # stop runtime timer for the job-server running on the selected processor
                if (cpu_min.running):
                    self.cbs_servers[cpu_min.running.task].timer_runtime.stop()

                return (job, cpu_min)

    def deadline_call(self, server):
        # This call is done when a CBS deadline expired
        # The runtime is refilled, a new deadline-server is computed and
        # the deadline-time is restarted
        if server.ready_list:
            server.set(server.maximum_runtime,
                       self.sim.now_ms() + server.period,
                       self.sim.now_ms(),
                       Timer(self.sim, SCHED_DEADLINE.deadline_call,
                             (self, server), server.deadline, one_shot=True,
                             cpu=self.processors[0], overhead=.000))
        server.task.cpu.resched()


    def runtime_call(self, server):
        # This call is done when the CBS runtime is consummed by a job-server
        # The state of the server becomes Throttled and the job is preempted
        server.is_throttled = True
        server.task.cpu.preempt()
        server.task.cpu.resched()


class CBSServer():
    def __init__(self, task, cbs_period, cbs_maximum_runtime, cbs_deadline):
        self.task = task
        self.period = cbs_period
        self.maximum_runtime = cbs_maximum_runtime
        self.deadline = cbs_deadline
        self.current_deadline = 0.
        self.current_runtime = 0.
        self.last_update = 0.
        self.ready_list = []
        self.is_throttled = False
        self.timer_runtime = None
        self.timer_deadline = None

    def __str__(self):
        st = ""
        st = "Server %s (%s,%s,%s) " % (self.task.name, self.maximum_runtime, self.period, self.deadline)
        st += " d:" + str(self.current_deadline) + " q:" + str(self.current_runtime)
        return st

    def add_job(self, job):
        self.ready_list.append(job)

    def remove_job(self, job):
        self.ready_list.remove(job)
        if (not self.ready_list):
            self.current_deadline = 0.
            self.current_runtime = 0.
            self.timer_deadline.stop()
            if self.timer_runtime:
                self.timer_runtime.stop()

    def set(self, q, d, time, timer_deadline):
        self.current_runtime = q
        self.current_deadline = d
        self.timer_deadline = timer_deadline
        self.timer_deadline.start()
        self.last_update = time
        self.is_throttled = False

    def update_runtime(self, time):
        self.current_runtime = self.current_runtime - (time - self.last_update)
        self.last_update = time
