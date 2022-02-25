Frequently Asked Questions
==========================

(please send me your questions in order to complete this list.)

Does it work on my operating system?
------------------------------------

SimSo is fully written in Python and depends on libraries that are available for Linux, Mac OS and Windows. If you install the dependencies, you can install SimSo using the source code. Otherwise, I also provide a debian/ubuntu package and a windows installer.

Can I use my own task generator?
--------------------------------

If you are using SimSo from a Python script, you can create the tasks easily with the characteristics of your choice.

If you are using the graphical user interface, you can generate an XML file compatible with SimSo. The XSD schema is shipped with the source code (it is incomplete though).


Does SimSo support sporadic tasks?
----------------------------------

This was implemented in July 2014. With sporadic tasks, you must specify the list of activation dates. This allows you to use an external generator to control the arrival of the jobs.

Do you handle uniform and/or heterogeneous processors?
------------------------------------------------------

It is possible to set a speed for each processor (uniform) but you can't specify task execution speed in function of the processor (heterogeneous). However, this could be done by adding a new Execution Time Model.
