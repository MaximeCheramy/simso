# List of all schedulers that have been declared using
# the @scheduler decorator.
__loaded_schedulers = []

# Decorator used to register a scheduler to be returned by get_declared_schedulers()
def scheduler(name, **kwargs):
	"""
	Decorator used to register a scheduler to be returned by get_declared_schedulers().
	Mandatory arguments : 
		name : the complete name of the scheduler (ex : simso.schedulers.EDF)
	Optional keyword arguments : 
		display_name : name to be shown to the user
		required_fields : list of required fields for this scheduler to work correctly.
			It should be a dict with the following keys : 
				name: name of the field
				type: type of the field
				default: default value of the field
		required_task_fields : list of required fields for this scheduler's tasks
			to work correctly. Same format as required_fields
		required_proc_fields : list of required fields for this scheduler's processors
			to work correctly. Same format as required_fields
				
	The list of registered schedulers is mostly used in graphical interfaces to auto-detect
	the exposed schedulers.
	"""
	required_fields = kwargs['required_fields'] if 'required_fields' in kwargs else []
	task_f = kwargs['required_task_fields'] if 'required_task_fields' in kwargs else []
	proc_f = kwargs['required_proc_fields'] if 'required_proc_fields' in kwargs else []
	display_name = kwargs['display_name'] if 'display_name' in kwargs else name
	def f(klass):
		# Note : 
		# We didn't include this data into the classes because it didn't work
		# properly with inheritance.
		# klass.simso_name = name
		# klass.simso_required_fields = required_fields
		# klass.simso_required_task_fields = task_f
		# klass.simso_required_proc_fields = proc_f
		__loaded_schedulers.append({
			'name': name,
			'display_name': display_name,
			'required_fields': required_fields,
			'required_task_fields': task_f,
			'required_proc_fields': proc_f
		})
		return klass
		
	return f

def get_loaded_schedulers():
	return __loaded_schedulers