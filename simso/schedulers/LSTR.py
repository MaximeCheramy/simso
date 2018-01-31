from simso.core import Scheduler, Timer
from simso.schedulers import scheduler


@scheduler("simso.schedulers.LSTR")
class LSTR(Scheduler):
    """
    Least Slack Time Rate First
    """

    def init(self):
        pass