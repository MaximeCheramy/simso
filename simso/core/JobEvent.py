# coding=utf-8


class JobEvent:
    ACTIVATE = 1
    EXECUTE = 2
    PREEMPTED = 3
    TERMINATED = 4
    ABORTED = 5

    count = 0

    def __init__(self, job, event, cpu=None):
        self.event = event
        self.job = job
        self.cpu = cpu
        JobEvent.count += 1
        self.id_ = JobEvent.count
