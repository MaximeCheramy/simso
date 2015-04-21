from setuptools import setup, find_packages
import simso

setup(
    name='simso',
    version=simso.__version__,
    description='Simulation of Multiprocessor Real-Time Scheduling with Overheads',
    author='Maxime Cheramy',
    author_email='maxime.cheramy@laas.fr',
    url='http://homepages.laas.fr/mcheramy/simso/',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering',
        'Development Status :: 5 - Production/Stable'
    ],
    packages=find_packages(),
    install_requires=[
        'SimPy==2.3.1',
        'numpy>=1.6'
    ],
    long_description="""\
SimSo is a scheduling simulator for real-time multiprocessor architectures that
takes into account some scheduling overheads (scheduling decisions, context-
switches) and the impact of caches through statistical models. Based on a
Discrete-Event Simulator, it allows quick simulations and a fast prototyping
of scheduling policies using Python."""
)
