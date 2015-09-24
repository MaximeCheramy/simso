How to write a scheduling policy
================================

This tutorial explains through minimalist examples how to write a scheduler.

.. contents:: Table of Contents

Example 1: uniprocessor EDF
---------------------------

This example shows how to write an Earliest Deadline First scheduler for a single processor. As a reminder, the Earliest Deadline First prioritizes the tasks with the closest absolute deadline among all the ready tasks. A task is ready when it is activated and not finished.

Creation of the file
""""""""""""""""""""

A scheduler for SimSo is a Python class that inherits from the :class:`simso.core.Scheduler` class. The first step is to write the skeleton of our scheduler. Create a file named "EDF_mono.py" and write the following code::

    from simso.core import Scheduler

    class EDF_mono(Scheduler):
        def init(self):
            pass

        def on_activate(self, job):
            pass

        def on_terminated(self, job):
            pass

        def schedule(self, cpu):
            pass

It is mandatory for the class name to be identical to the file name.

Explanation of the skeleton
"""""""""""""""""""""""""""

The first thing done here is importing the :class:`Scheduler <simso.core.Scheduler>` class. Then we define the `EDF_mono` class as a subclass of the `Scheduler`. 

Four methods are redifined:

- The :meth:`init <simso.core.Scheduler.Scheduler.init>` method is called when the simulation is ready to start, this is where the structures used by the scheduler should be initialized. The usual Python constructor is not guaranteed to be called before each simulation run and the :class:`Task <simso.core.Task.Task>` and :class:`Processors <simso.core.Processor.Processor>` are not instantiated yet when the scheduler is created.

- The :meth:`on_activate <simso.core.Scheduler.Scheduler.on_activate>` method is called on task activations.

- The :meth:`on_terminated <simso.core.Scheduler.Scheduler.on_terminated>` method is called when a job finished its execution.

- The :meth:`schedule <simso.core.Scheduler.Scheduler.schedule>` method is called by the processor when it needs to run the scheduler. This method should not be called directly.

Implementation
""""""""""""""

In a nutshell, the algorithm is the following: a list of ready jobs is kept up-to-date using the `on_activate` and `on_terminated` methods. When the schedule method is called, the ready job with the closest absolute deadline is chosen.

So, the first step is to define a `ready_list`, and to append the jobs and remove them respectively when the jobs are activated and when they finish. The code should looks like that::

    from core import Scheduler

    class EDF_mono(Scheduler):
        def init(self):
            self.ready_list = []

        def on_activate(self, job):
            self.ready_list.append(job)

        def on_terminated(self, job):
            self.ready_list.remove(job)

        def schedule(self, cpu):
            pass


The second step is to write the schedule logic. Selecting the job with the closest absolute deadline is pretty easy. But we need to be sure that there is at least one ready job. One possible implementation is::

        def schedule(self, cpu):
            if self.ready_list:  # If at least one job is ready:
                # job with the highest priority
                job = min(self.ready_list, key=lambda x: x.absolute_deadline)
            else:
                job = None
            
            return (job, cpu)

At this point, we are still missing a very important thing: calling the scheduler! This is not done by invoking the `schedule` method. As a reminder, that's the processor which is responsible to call the `scheduler`. The reason is that if an overhead must be applied, it is done on the processor running the scheduler. The good way to call the scheduler is by sending a message to the processor using the :meth:`resched <simso.core.Processor.Processor.resched>` method.

Any job is affected to a processor. This is the last processor on which the task was running or an arbitrary processor on the first execution. The scheduler can be called indirectly using ``job.cpu.resched()`` when a scheduling event occurs. We could also use ``self.processors[0].resched`` to run the scheduler on the first (and only) processor of the system.

This is the full code::

    from simso.core import Scheduler
    
    
    class EDF_mono(Scheduler):
        def init(self):
            self.ready_list = []
    
        def on_activate(self, job):
            self.ready_list.append(job)
            job.cpu.resched()
    
        def on_terminated(self, job):
            self.ready_list.remove(job)
            job.cpu.resched()
    
        def schedule(self, cpu):
            if self.ready_list:  # If at least one job is ready:
                # job with the highest priority
                job = min(self.ready_list, key=lambda x: x.absolute_deadline)
            else:
                job = None
            
            return (job, cpu)

Example 2: Partitionned EDF
---------------------------

The simplest method to handle multiprocessor architectures is to use partitionning. This approach consists in allocating the tasks to the processors and executing a mono-processor scheduler on each processor.

In order to ease the work for the developer of a scheduler, an helping class, named :class:`PartitionedScheduler <simso.utils.PartitionedScheduler>`, is provided.

Initializing the scheduler
""""""""""""""""""""""""""

The :class:`PartitionedScheduler <simso.utils.PartitionedScheduler>` is defined in the `simso.utils` module. It is also necessary to load the :class:`SchedulerInfo <simso.core.Scheduler.SchedulerInfo>` class in order to give to the `PartitionedScheduler <simso.utils.PartitionedScheduler>` the mono-processor scheduler to use. The first thing to do is importing these classes::

    from simso.utils import PartitionedScheduler
    from simso.core.Scheduler import SchedulerInfo

Then the Scheduler can be initialized like this::

        class P_EDF(PartitionedScheduler):
            def init(self):
                PartitionedScheduler.init(self, SchedulerInfo("EDF_mono", EDF_mono))


Defining the packing
""""""""""""""""""""

A First-Fit bin-packing can be used to affect the tasks to the processors. For that, the :meth:`packer` must be overriden::

            def packer(self):
                # First Fit
                cpus = [[cpu, 0] for cpu in self.processors]
                for task in self.task_list:
                    j = 0
                    # Find a processor with free space.
                    while cpus[j][1] + float(task.wcet) / task.period > 1.0:
                        j += 1
                        if j >= len(self.processors):
                            print("oops bin packing failed.")
                            return False

                    # Affect it to the task.
                    self.affect_task_to_processor(task, cpus[j][0])

                    # Update utilization.
                    cpus[j][1] += float(task.wcet) / task.period
                return True


Complete example
""""""""""""""""

Complete source code::

        from simso.core.Scheduler import SchedulerInfo
        from EDF_mono import EDF_mono
        from simso.utils import PartitionedScheduler


        class P_EDF(PartitionedScheduler):
            def init(self):
                PartitionedScheduler.init(self, SchedulerInfo("EDF_mono", EDF_mono))

            def packer(self):
                # First Fit
                cpus = [[cpu, 0] for cpu in self.processors]
                for task in self.task_list:
                    j = 0
                    # Find a processor with free space.
                    while cpus[j][1] + float(task.wcet) / task.period > 1.0:
                        j += 1
                        if j >= len(self.processors):
                            print("oops bin packing failed.")
                            return False

                    # Affect it to the task.
                    self.affect_task_to_processor(task, cpus[j][0])

                    # Update utilization.
                    cpus[j][1] += float(task.wcet) / task.period
                return True

