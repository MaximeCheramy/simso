def GFB(configuration):
    """
    Sufficient test for Global-EDF.
    """
    umax = max(t.wcet / t.deadline for t in configuration.task_info_list)
    utot = sum(t.wcet / t.deadline for t in configuration.task_info_list)
    m = len(configuration.proc_info_list)

    return utot <= m * (1 - umax) + umax


def BAK(configuration):
    """
    Sufficient test for Global-EDF. This code is untested.
    """
    m = len(configuration.proc_info_list)

    def b(task, task_k):
        lk = task_k.wcet / task_k.deadline
        ui = task.wcet / task.period
        if lk >= ui:
            return ui * (1 + (task.period - task.deadline) / task_k.deadline)
        else:
            return ui * (1 + (task.period - task.deadline) / task_k.deadline) \
                + (task.wcet - lk * task.period) / task_k.deadline

    def cond(task):
        s = sum(min(1, b(i, task)) for i in configuration.task_info_list)
        lk = task.wcet / task.deadline
        return s <= m * (1 - lk) + lk

    return all(cond(k) for k in configuration.task_info_list)
