Introduction
============

What is SimSo?
--------------

SimSo is a scheduling simulator for real-time multiprocessor architectures that takes into account some scheduling overheads (scheduling decisions, context switches) and the impact of caches through statistical models. Based on a Discrete-Event Simulator (SimPy), it allows quick simulations and a fast prototyping of scheduling policies using Python.

SimSo is an open source software, available under the `CeCILL license <licenses.html>`_, a GPL compatible license.

Download
--------

You can find the last version of SimSo on the `SimSo Website`_.

.. _Simso Website: http://homepages.laas.fr/mcheramy/simso/

Installation
------------

SimSo is available for the main platforms and so is its source code. The archive containing the source code is more often updated and should be used when possible.

In order to install SimSo from the souce code, the dependences must be installed first. Then, type "python setup.py install" to install SimSo.

Dependencies
""""""""""""

When using SimSo from the sources, the following softwares and librairies are required:

    - Python 2.7+
    - SimPy 2.3.1 (not compatible with SimPy 3)
    - NumPy 1.6+
    - PyQt4 4.9+

If you are using a binary, everything should be packed in the binary.

First step
----------

SimSo is provided with a graphical user interface that aims to be very easy to use. This is a good way to develop and test a scheduler. See `How to write a scheduling policy <write_scheduler.html>`_.

It is also possible to use SimSo as a library. This allows in particular to run simulations in text mode with a maximum of flexibility.

Available Schedulers
--------------------

Currently, the following schedulers are available:

**Uniprocessor schedulers**

    - Earliest Deadline First (EDF)
    - Rate Monotonic (RM)
    - Fixed Priority (FP)
    - Static-EDF (A DVFS EDF)
    - CC-EDF: Real-Time dynamic voltage scaling for low-power embedded operating systems by P. Pillai et al.

**Uniprocessor schedulers adapted to multiprocessor**
    - Global-EDF
    - Global-RM
    - Earliest Deadline Zero Laxity (EDZL)
    - Least Laxity First (LLF)
    - Modified Least Laxity First (MLLF): A Modified Least-Laxity-First Scheduling Algorithm for Real-Time Tasks by S.-H. Oh and S.-M. Yang.
    - PriD: Real-time scheduling on multiprocessors by J., Baruah, S., & Funk, S.
    - EDF-US
    - G-FL: Fair lateness scheduling: Reducing maximum lateness in G-EDF-like scheduling by Erickson and Anderson.

**Partitionned**
    Any uniprocessor scheduler using a partitionning algorithm. The following heuristics are provided:

    - First-Fit and Decreasing-First-Fit
    - Next-Fit and Decreasing-Next-Fit
    - Best-Fit and Decreasing-Best-Fit
    - Worst-Fit and Decreasing-Worst-Fit

**PFair**
    - Earliest Pseudo-Deadline First (EPDF)
    - PD2 and ER-PD2: Early-Release Fair Scheduling. In Proceedings of the Euromicro Conference on Real-Time Systems by J. H. Anderson et al.

**DPFair**
    - LLREF: An Optimal Real-Time Scheduling Algorithm for Multiprocessors by Cho et al.
    - LRE-TL:  An Optimal Multiprocessor Scheduling Algorithm for Sporadic Task Sets by S. Funk et al.
    - DP-WRAP: DP-FAIR: A Simple Model for Understanding Optimal Multiprocessor Scheduling by Levin et al.
    - BF: Multiple-resource periodic scheduling problem: how much fairness is necessary? by Zhu et al.
    - NVNLF: Work-Conversing Optimal Real-Time Scheduling on Multiprocessors by Funaoka et al.

**Semi-partitionned**
    - EKG:  Multiprocessor Scheduling with Few Preemptions by B. Andersson and E. Tovar. 
    - EDHS: Semi-Partitioning Technique for Multiprocessor Real-Time Scheduling by Kato et al.

**Other**
    - RUN: Optimal Multiprocessor Real-Time Scheduling via Reduction to Uniprocessor by Regnier et al.
    - U-EDF: an Unfair but Optimal Multiprocessor Scheduling Algorithm for Sporadic Tasks by Nelissen et al.
