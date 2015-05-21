"""
This module is part of the RUN implementation (see RUN.py).
"""

from fractions import Fraction


class _Server(object):
    """
    Abstract class that represents a Server.
    """
    next_id = 1

    def __init__(self, is_dual, task=None):
        self.parent = None
        self.is_dual = is_dual
        self.utilization = Fraction(0, 1)
        self.task = task
        self.job = None
        self.deadlines = [0]
        self.budget = 0
        self.next_deadline = 0
        self.identifier = _Server.next_id
        _Server.next_id += 1
        if task:
            if hasattr(task, 'utilization'):
                self.utilization += task.utilization
            else:
                self.utilization += Fraction(task.wcet) / Fraction(task.period)

    def add_deadline(self, current_instant, deadline):
        """
        Add a deadline to this server.
        """
        self.deadlines.append(deadline)

        self.deadlines = [d for d in self.deadlines if d > current_instant]
        self.next_deadline = min(self.deadlines)

    def create_job(self, current_instant):
        """
        Replenish the budget.
        """
        self.budget = int(self.utilization * (self.next_deadline -
                          current_instant))


class TaskServer(_Server):
    """
    A Task Server is a Server that contains a real Task.
    """
    def __init__(self, task):
        super(TaskServer, self).__init__(False, task)


class EDFServer(_Server):
    """
    An EDF Server is a Server with multiple children scheduled with EDF.
    """
    def __init__(self):
        super(EDFServer, self).__init__(False)
        self.children = []

    def add_child(self, server):
        """
        Add a child to this EDFServer (used by the packing function).
        """
        self.children.append(server)
        self.utilization += server.utilization
        server.parent = self


class DualServer(_Server):
    """
    A Dual server is the opposite of its child.
    """
    def __init__(self, child):
        super(DualServer, self).__init__(True)
        self.child = child
        child.parent = self
        self.utilization = 1 - child.utilization


def add_job(sim, job, server):
    """
    Recursively update the deadlines of the parents of server.
    """
    server.job = job
    while server:
        server.add_deadline(sim.now(), job.absolute_deadline *
                            sim.cycles_per_ms)
        server.create_job(sim.now())
        server = server.parent


def select_jobs(server, virtual, execute=True):
    """
    Select the jobs that should run according to RUN. The virtual jobs are
    appended to the virtual list passed as argument.
    """
    jobs = []
    if execute:
        virtual.append(server)

    if server.task:
        if execute and server.budget > 0 and server.job.is_active():
            jobs.append(server.job)
    else:
        if server.is_dual:
            jobs += select_jobs(server.child, virtual, not execute)
        else:
            active_servers = [s for s in server.children if s.budget > 0]
            if active_servers:
                min_server = min(active_servers, key=lambda s: s.next_deadline)
            else:
                min_server = None

            for child in server.children:
                jobs += select_jobs(child, virtual,
                                    execute and child is min_server)

    return jobs


def get_child_tasks(server):
    """
    Get the tasks scheduled by this server.
    """
    if server.task:
        return [server]
    else:
        if server.is_dual:
            return get_child_tasks(server.child)
        else:
            tasks = []
            for child in server.children:
                tasks += get_child_tasks(child)
            return tasks
