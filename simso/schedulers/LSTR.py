from simso.core import Scheduler, Timer
from simso.schedulers import scheduler


@scheduler("simso.schedulers.LSTR")
class LSTR(Scheduler):
    """
    Least Slack Time Rate First
    """

    def init(self):
        self.ready_list = []
        """
        However, LSTR
        scheduling algorithm operates on every basic time unit. Here, we consider the basic
        time unit of 1 (ms).
        """
        self.timer = Timer(self.sim, LSTR.virtual_event,
                           (self, self.processors[0]), 1, one_shot=False)
        self.timer.start()

    def virtual_event(self, cpu):
        self.reschedule(cpu)

    def reschedule(self, cpu):
        if self.ready_list:
            cpu.resched()

    def LSTR_rank(self, job):
        """
        calculates rank described in LSTR algorithm for given job
        return value should be non-negative, negative value means that job has passed deadline
        """
        if not job:
            return 0
        # print(job.absolute_deadline, job.deadline)
        din = job.absolute_deadline - self.sim.now_ms()
        if din == 0:
            return 0
        return job.ret / din

    def on_activate(self, job):
        self.ready_list.append(job)
        self.reschedule(job.cpu)

    def on_terminated(self, job):
        self.ready_list.remove(job)
        self.reschedule(job.cpu)

    def schedule(self, cpu):
        decision = []
        if self.ready_list:
            self.ready_list.sort(key=self.LSTR_rank, reverse=True)
            number_of_processors = len(self.processors)
            jobs = self.ready_list[:number_of_processors]

            available_proc = [p for p in self.processors if p.running not in jobs]
            for job in jobs:
                if job.is_running():
                    continue
                for cpu in available_proc:
                    job_on_cpu_rank = self.LSTR_rank(cpu.running)
                    if job_on_cpu_rank < self.LSTR_rank(job):
                        decision.append((job, cpu))
                        available_proc.remove(cpu)
                        break
        return decision
