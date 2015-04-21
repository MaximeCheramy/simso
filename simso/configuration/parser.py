# coding=utf-8

from xml.dom.minidom import parse
import os.path
from simso.core.Task import TaskInfo, task_types
from simso.core.Processor import ProcInfo
from simso.core.Caches import Cache_LRU
from simso.core.Scheduler import SchedulerInfo


convert_function = {
    'int': int,
    'float': float,
    'bool': bool,
    'str': str
}


class Parser(object):
    """
    Simulation file parser.
    """
    def __init__(self, filename):
        self.filename = filename
        self.cur_dir = os.path.split(filename)[0]
        if not self.cur_dir:
            self.cur_dir = '.'
        self._dom = parse(filename)
        self._parse_etm()
        self._parse_duration()
        self._parse_cycles_per_ms()
        self._parse_caches()
        self._parse_tasks()
        self._parse_processors()
        self._parse_scheduler()
        self._parse_penalty()

    def _parse_caches(self):
        self.caches_list = []
        caches_element = self._dom.getElementsByTagName('caches')[0]
        caches = caches_element.getElementsByTagName('cache')
        attr = caches_element.attributes

        self.memory_access_time = 100
        if 'memory_access_time' in attr:
            self.memory_access_time = int(attr['memory_access_time'].value)

        for cache in caches:
            attr = cache.attributes
            if attr['policy'].value == 'LRU' and attr['type'].value == 'data':
                access_time = 1
                associativity = int(attr['size'].value)
                if 'access_time' in attr:
                    access_time = int(attr['access_time'].value)
                if 'associativity' in attr:
                    associativity = int(attr['associativity'].value)
                cache = Cache_LRU(attr['name'].value, int(attr['id'].value),
                                  int(attr['size'].value), associativity,
                                  access_time)
                self.caches_list.append(cache)
            # TODO Généraliser aux autres types de cache.

    def _parse_tasks(self):
        tasks_el = self._dom.getElementsByTagName('tasks')[0]

        self.task_data_fields = {}
        for field in tasks_el.getElementsByTagName('field'):
            attr = field.attributes
            self.task_data_fields[attr['name'].value] = attr['type'].value

        tasks = tasks_el.getElementsByTagName('task')
        self.task_info_list = []
        for task in tasks:
            attr = task.attributes

            data = dict(
                (k, convert_function[self.task_data_fields[k]](attr[k].value))
                for k in attr.keys() if k in self.task_data_fields)

            task_type = 'Periodic'
            if 'task_type' in attr and attr['task_type'].value in task_types:
                task_type = attr['task_type'].value
            elif 'periodic' in attr and attr['periodic'].value == 'no':
                task_type = 'APeriodic'

            list_activation_dates = []
            if 'list_activation_dates' in attr and attr['list_activation_dates'].value != '':
                list_activation_dates = sorted(
                    map(float, attr['list_activation_dates'].value.split(',')))

            t = TaskInfo(
                attr['name'].value,
                int(attr['id'].value),
                task_type,
                'abort_on_miss' in attr
                and attr['abort_on_miss'].value == 'yes',
                float(attr['period'].value),
                float(attr['activationDate'].value)
                if 'activationDate' in attr else 0,
                int(attr['instructions'].value),
                float(attr['mix'].value),
                (self.cur_dir + '/' + attr['stack'].value,
                    self.cur_dir) if 'stack' in attr else ("", self.cur_dir),
                float(attr['WCET'].value),
                float(attr['ACET'].value) if 'ACET' in attr else 0,
                float(attr['et_stddev'].value) if 'et_stddev' in attr else 0,
                float(attr['deadline'].value),
                float(attr['base_cpi'].value),
                int(attr['followed_by'].value)
                if 'followed_by' in attr else None,
                list_activation_dates,
                int(float(attr['preemption_cost'].value))
                if 'preemption_cost' in attr else 0,
                data)
            self.task_info_list.append(t)

    def _parse_processors(self):
        processors_el = self._dom.getElementsByTagName('processors')[0]
        processors = self._dom.getElementsByTagName('processors')[0]
        attr = processors.attributes

        migration_overhead = 0
        if 'migration_overhead' in attr:
            migration_overhead = int(attr['migration_overhead'].value)

        self.proc_data_fields = {}
        for field in processors_el.getElementsByTagName('field'):
            attr = field.attributes
            self.proc_data_fields[attr['name'].value] = attr['type'].value

        cpus = processors.getElementsByTagName('processor')
        self.proc_info_list = []
        for cpu in cpus:
            attr = cpu.attributes

            data = dict(
                (k, convert_function[self.proc_data_fields[k]](attr[k].value))
                for k in attr.keys() if k in self.proc_data_fields)

            cl_overhead = 0
            cs_overhead = 0
            if 'cl_overhead' in attr:
                cl_overhead = int(float(attr['cl_overhead'].value))
            if 'cs_overhead' in attr:
                cs_overhead = int(float(attr['cs_overhead'].value))

            speed = 1.0
            if 'speed' in attr:
                speed = float(attr['speed'].value)

            proc = ProcInfo(name=attr['name'].value,
                            identifier=int(attr['id'].value),
                            cs_overhead=cs_overhead,
                            cl_overhead=cl_overhead,
                            migration_overhead=migration_overhead,
                            speed=speed,
                            data=data)

            caches = cpu.getElementsByTagName('cache')
            for cache_element in caches:
                attr = cache_element.attributes
                for cache in self.caches_list:
                    if cache.identifier == int(attr['ref'].value):
                        proc.add_cache(cache)

            self.proc_info_list.append(proc)

    def _parse_etm(self):
        simulation = self._dom.getElementsByTagName('simulation')[0]

        if 'etm' in simulation.attributes:
            self.etm = simulation.attributes['etm'].value
        else:
            use_wcet = True
            if 'use_wcet' in simulation.attributes:
                use_wcet = (simulation.attributes['use_wcet'].value
                            in ('true', 'yes'))
            if use_wcet:
                self.etm = "wcet"
            else:
                self.etm = "cache"

    def _parse_duration(self):
        simulation = self._dom.getElementsByTagName('simulation')[0]
        if 'duration' in simulation.attributes:
            self.duration = int(simulation.attributes['duration'].value)
        else:
            self.duration = 50000

    def _parse_penalty(self):
        simulation = self._dom.getElementsByTagName('simulation')[0]
        if 'penalty_preemption' in simulation.attributes:
            self.penalty_preemption = int(
                simulation.attributes['penalty_preemption'].value)
        else:
            self.penalty_preemption = 100000
        if 'penalty_migration' in simulation.attributes:
            self.penalty_migration = int(
                simulation.attributes['penalty_migration'].value)
        else:
            self.penalty_migration = 100000

    def _parse_cycles_per_ms(self):
        simulation = self._dom.getElementsByTagName('simulation')[0]
        if 'cycles_per_ms' in simulation.attributes:
            self.cycles_per_ms = int(
                simulation.attributes['cycles_per_ms'].value)
        else:
            self.cycles_per_ms = 1000000

    def _parse_scheduler(self):
        overhead = 0
        overhead_activate = 0
        overhead_terminate = 0
        sched = self._dom.getElementsByTagName('sched')[0]
        attr = sched.attributes
        filename = attr['className'].value
        if 'overhead' in attr:
            overhead = int(float(attr['overhead'].value))
        if 'overhead_activate' in attr:
            overhead_activate = int(float(attr['overhead_activate'].value))
        if 'overhead_terminate' in attr:
            overhead_terminate = int(float(attr['overhead_terminate'].value))

        data = {}
        fields = sched.getElementsByTagName('field')
        for field in fields:
            name = field.attributes['name'].value
            type_ = field.attributes['type'].value
            value = field.attributes['value'].value
            data[name] = (convert_function[type_](value), type_)

        self.scheduler_info = SchedulerInfo(
            overhead=overhead, overhead_activate=overhead_activate,
            overhead_terminate=overhead_terminate, fields=data)
        if filename[0] != '/':
                filename = self.cur_dir + '/' + filename
        self.scheduler_info.set_name(filename, self.cur_dir)
