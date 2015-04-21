#!/usr/bin/python
# coding=utf-8

from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree
from xml.dom import minidom


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t")


def generate(configuration):
    """
    Generate a string containing the XML version of the configuration.
    """
    attrs = {'duration': str(int(configuration.duration)),
             'cycles_per_ms': str(configuration.cycles_per_ms),
             'etm': str(configuration.etm)}
    top = Element('simulation', attrs)

    generate_sched(top, configuration.scheduler_info)
    generate_cache(
        top, configuration.caches_list, configuration.memory_access_time)
    generate_processors(
        top, configuration.proc_info_list, configuration.proc_data_fields)
    generate_tasks(
        top, configuration.task_info_list, configuration.task_data_fields)

    return prettify(top)


def generate_sched(top, sched_info):
    sched = SubElement(top, 'sched', {
        'className': sched_info.name,
        'overhead': str(sched_info.overhead),
        'overhead_activate': str(sched_info.overhead_activate),
        'overhead_terminate': str(sched_info.overhead_terminate)
    })
    for field_name in sched_info.data.keys():
        SubElement(sched, 'field', {'name': field_name,
                                    'value': str(sched_info.data[field_name]),
                                    'type': sched_info.fields_types[field_name]
                                    })
    return sched


def generate_cache(top, caches_list, memory_access_time):
    caches = SubElement(top, 'caches',
                        {'memory_access_time': str(memory_access_time)})
    for cache in caches_list:
        SubElement(caches, 'cache', {'name': cache.name,
                                     'id': str(cache.identifier),
                                     'policy': "LRU",  # TODO
                                     'type': "data",  # TODO
                                     'size': str(cache.size),
                                     'access_time': str(cache.access_time)})
    return caches


def generate_processors(top, proc_info_list, fields):
    processors = SubElement(top, 'processors')

    for name, ftype in fields.items():
        attrs = {'name': name, 'type': ftype}
        SubElement(processors, 'field', attrs)

    for proc in proc_info_list:
        attrs = dict((k, str(proc.data[k])) for k in proc.data.keys())
        attrs.update({
            'name': proc.name,
            'id': str(proc.identifier),
            'cl_overhead': str(proc.cl_overhead),
            'cs_overhead': str(proc.cs_overhead),
            'speed': str(proc.speed)})
        processor = SubElement(processors, 'processor', attrs)
        for cache in proc.caches:
            SubElement(processor, 'cache', {'ref': str(cache.identifier)})


def generate_tasks(top, task_info_list, fields):
    tasks = SubElement(top, 'tasks')

    for name, ftype in fields.items():
        attrs = {'name': name, 'type': ftype}
        SubElement(tasks, 'field', attrs)

    for task in task_info_list:
        attrs = dict((k, str(task.data[k])) for k in task.data.keys())
        attrs.update({'name': task.name,
                      'id': str(task.identifier),
                      'task_type': task.task_type,
                      'abort_on_miss': 'yes' if task.abort_on_miss else 'no',
                      'period': str(task.period),
                      'activationDate': str(task.activation_date),
                      'list_activation_dates': ', '.join(
                          map(str, task.list_activation_dates)),
                      'deadline': str(task.deadline),
                      'base_cpi': str(task.base_cpi),
                      'instructions': str(task.n_instr),
                      'mix': str(task.mix),
                      'WCET': str(task.wcet),
                      'ACET': str(task.acet),
                      'preemption_cost': str(task.preemption_cost),
                      'et_stddev': str(task.et_stddev)})
        if task.followed_by is not None:
            attrs['followed_by'] = str(task.followed_by)
        if task.stack_file:
            # XXX: what if the path contain a non-ascii character?
            attrs['stack'] = str(task.stack_file)
        SubElement(tasks, 'task', attrs)
