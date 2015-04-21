# coding=utf-8


class ProcEvent(object):
    RUN = 1
    IDLE = 2
    OVERHEAD = 3

    def __init__(self, event=0, args=None):
        self.event = event
        self.args = args


class ProcRunEvent(ProcEvent):
    def __init__(self, job):
        ProcEvent.__init__(self, ProcEvent.RUN, job)


class ProcIdleEvent(ProcEvent):
    def __init__(self):
        ProcEvent.__init__(self, ProcEvent.IDLE)


class ProcOverheadEvent(ProcEvent):
    def __init__(self, type_overhead):
        ProcEvent.__init__(self, ProcEvent.OVERHEAD, type_overhead)


class ProcCxtSaveEvent(ProcOverheadEvent):
    def __init__(self, terminated=False):
        ProcOverheadEvent.__init__(self, "CS")
        self.terminated = terminated


class ProcCxtLoadEvent(ProcOverheadEvent):
    def __init__(self, terminated=False):
        ProcOverheadEvent.__init__(self, "CL")
        self.terminated = terminated
