# coding=utf-8


class SchedulerEvent(object):
    BEGIN_SCHEDULE = 1
    END_SCHEDULE = 2
    BEGIN_ACTIVATE = 3
    END_ACTIVATE = 4
    BEGIN_TERMINATE = 5
    END_TERMINATE = 6

    def __init__(self, cpu):
        self.event = 0
        self.cpu = cpu


class SchedulerBeginScheduleEvent(SchedulerEvent):
    def __init__(self, cpu):
        SchedulerEvent.__init__(self, cpu)
        self.event = SchedulerEvent.BEGIN_SCHEDULE


class SchedulerEndScheduleEvent(SchedulerEvent):
    def __init__(self, cpu):
        SchedulerEvent.__init__(self, cpu)
        self.event = SchedulerEvent.END_SCHEDULE


class SchedulerBeginActivateEvent(SchedulerEvent):
    def __init__(self, cpu):
        SchedulerEvent.__init__(self, cpu)
        self.event = SchedulerEvent.BEGIN_ACTIVATE


class SchedulerEndActivateEvent(SchedulerEvent):
    def __init__(self, cpu):
        SchedulerEvent.__init__(self, cpu)
        self.event = SchedulerEvent.END_ACTIVATE


class SchedulerBeginTerminateEvent(SchedulerEvent):
    def __init__(self, cpu):
        SchedulerEvent.__init__(self, cpu)
        self.event = SchedulerEvent.BEGIN_TERMINATE


class SchedulerEndTerminateEvent(SchedulerEvent):
    def __init__(self, cpu):
        SchedulerEvent.__init__(self, cpu)
        self.event = SchedulerEvent.END_TERMINATE
