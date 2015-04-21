# coding=utf-8

from SimPy.Simulation import Process, hold

# TODO: allow the user to specify an overhead.


class InstanceTimer(Process):
    def __init__(self, timer):
        Process.__init__(self, name="Timer", sim=timer.sim)
        self.function = timer.function
        self.args = timer.args
        self.delay = timer.delay
        self.one_shot = timer.one_shot
        self.cpu = timer.cpu
        self.running = False
        self.overhead = timer.overhead

    def call_handler(self):
        if self.running:
            self.function(*self.args)

    def run(self):
        self.running = True
        while self.running:
            yield hold, self, self.delay
            if self.interrupted() or not self.running:
                break
            if self.cpu:
                self.cpu.timer(self)
            else:
                self.call_handler()
            if self.one_shot:
                break


class Timer(object):
    """
    Allow to declare a timer. A timer is a mechanism that allows to call a
    function after a certain amount of time, periodically or single shot.

    A Timer can be used with or without specifying a processor. If a processor
    is specified, when the timer fire, if a job was running on the processor,
    it is temporarly interrupted. This is more realistic, even if for the
    moment there is no overhead associated to this action. A scheduler using a
    timer should define on which processor the callback will execute.

    The delay is expressed in milliseconds by default but it can also be given
    in cycles.
    """
    def __init__(self, sim, function, args, delay, one_shot=True, prior=False,
                 cpu=None, in_ms=True, overhead=0):
        """
        Args:
            - `sim`: The :class:`model <simso.core.Model.Model>` object.
            - `function`: Callback function, called when the delay expires.
            - `args`: Arguments passed to the callback function.
            - `delay`: Time to wait before calling the function.
            - `one_shot`: True if the timer should execute only once.
            - `prior`: If true, for the same date, the simulation should \
            start by handling the timer (should probably not be True).
            - `cpu`: On which :class:`processor \
            <simso.core.Processor.Processor>` the function is virtually \
            executing.
            - `in_ms`: True if the delay is expressed in millisecond. In \
            cycles otherwise.

        Methods:
        """
        self.sim = sim
        self.function = function
        self.args = args
        if in_ms:
            self.delay = int(delay * sim.cycles_per_ms)
        else:
            self.delay = int(delay)
        self.one_shot = one_shot
        self.prior = prior
        self.cpu = cpu
        self.instance = None
        if in_ms:
            self.overhead = int(overhead * sim.cycles_per_ms)
        else:
            self.overhead = int(overhead)
        assert self.delay >= 0, "delay must be >= 0"

    def start(self):
        """
        Start the timer.
        """
        self.instance = InstanceTimer(self)
        self.sim.activate(self.instance, self.instance.run(), self.prior)

    def stop(self):
        """
        Stop the timer.
        """
        if self.instance:
            self.instance.running = False
