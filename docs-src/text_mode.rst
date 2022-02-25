Using SimSo in script mode
==========================

SimSo can be used as a library in order to automatize wide experimentations and have a maximum of flexibility on the analysis of the results. In this tutorial, a few examples are provided.

.. contents:: Table of Contents


Loading a configuration using a simulation file
-----------------------------------------------

A :class:`Configuration <simso.configuration.Configuration>` can be initialized with a file passed to its constructor::

        configuration = Configuration(argv[1])

The configuration could also be partial and completed by the script. Finally, the configuration can be checked for correctness using the :meth:`check_all <simso.configuration.Configuration.check_all>` method::

        configuration.check_all()

This method will raise an exception if something is not correct.

Creating a configuration from scratch
-------------------------------------

It is also possible to create a new configuration from an empty configuration. This is done by instantiating a :class:`Configuration <simso.configuration.Configuration>` object without argument. Then, its attributes can be changed::

            configuration = Configuration()
            
            configuration.duration = 100 * configuration.cycles_per_ms

It is also possible to add tasks::

            configuration.add_task(name="T1", identifier=1, period=7,
                                   activation_date=0, wcet=3, deadline=7)

And of course processors::

            configuration.add_processor(name="CPU 1", identifier=1)

Finally, a scheduler is also required. For that, it's possible to use a custom scheduler::

            configuration.scheduler_info.filename = "examples/RM.py"

Or one of the schedulers embedded with SimSo::

            configuration.scheduler_info.clas = "simso.schedulers.RM"


Creating the Model
------------------

A :class:`configuration <simso.configuration.Configuration>` is an object grouping every characteristics of the system (tasks, processors, schedulers, etc). Such a configuration can be passed to the :class:`Model <simso.core.Model.Model>` constructor in order to create the simulation::

        model = Model(configuration)

And the simulation can be run with the :meth:`run_model <simso.core.Model.Model.run_model>` method::

        model.run_model()

Some basic logs can be get through the :meth:`logs <simso.core.Model.Model.logs>` attribute::

        for log in model.logs:
            print(log)

First Example
-------------

The following script simulate a system loading from a simulation file or configured from scratch::

        import sys
        from simso.core import Model
        from simso.configuration import Configuration


        def main(argv):
            if len(argv) == 2:
                # Configuration load from a file.
                configuration = Configuration(argv[1])
            else:
                # Manual configuration:
                configuration = Configuration()
                
                configuration.duration = 420 * configuration.cycles_per_ms

                # Add tasks:
                configuration.add_task(name="T1", identifier=1, period=7,
                                       activation_date=0, wcet=3, deadline=7)
                configuration.add_task(name="T2", identifier=2, period=12,
                                       activation_date=0, wcet=3, deadline=12)
                configuration.add_task(name="T3", identifier=3, period=20,
                                       activation_date=0, wcet=5, deadline=20)

                # Add a processor:
                configuration.add_processor(name="CPU 1", identifier=1)

                # Add a scheduler:
                #configuration.scheduler_info.filename = "examples/RM.py"
                configuration.scheduler_info.clas = "simso.schedulers.RM"

            # Check the config before trying to run it.
            configuration.check_all()

            # Init a model from the configuration.
            model = Model(configuration)

            # Execute the simulation.
            model.run_model()

            # Print logs.
            for log in model.logs:
                print(log)

        main(sys.argv)


More details
------------

It is possible to get more information from the tasks using :class:`Results <simso.core.results.Results>` class. For example we could get the computation time of the jobs::

            for task in model.results.tasks:
                print(task.name + ":")
                for job in task.jobs:
                    print("%s %.3f ms" % (job.name, job.computation_time))

Or the number of preemptions per task::

            for task in model.results.tasks.values():
                print("%s %s" % (task.name, task.preemption_count))

You can get all the metrics provided in the :class:`TaskR <simso.core.results.TaskR>` and :class:`JobR <simso.core.results.JobR>` objects. Read the documentation of these classes to know exactly what is directly accessible.

It is also possible to get the monitor object from each processors. This is a very detail history of the system. For example, you can count the number of context switches, where a context switch is something that happen when the previous task running on the same processor is different::

        cxt = 0
        for processor in model.processors:
            prev = None
            for evt in processor.monitor:
                if evt[1].event == ProcEvent.RUN:
                    if prev is not None and prev != evt[1].args.task:
                        cxt += 1
                    prev = evt[1].args.task

        print("Number of context switches (without counting the OS): " + str(cxt))
