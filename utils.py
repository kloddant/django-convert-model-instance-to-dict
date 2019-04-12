from django.db.models.fields import DateField, DateTimeField, TimeField
from django.db.models.fields.related import ForeignKey, OneToOneField, ManyToManyField
from django.db.models.fields.reverse_related import ManyToOneRel
from django.db.models.fields.files import FileField, ImageField

def convert_model_instance_to_dict(instance, func_name="dict", callers=set(), fields=[]):
	if not instance.pk:
		return {}

	callers = set(callers) #copy the callers to a new variable so that it doesn't modify the parent's callers.
	if type(instance) in callers:
		return {}
	callers.add(type(instance))

	response = {}

	model = type(instance)

	def handle_date_field(instance, field_name):
		value = getattr(instance, field_name)
		return value.strftime("%Y-%m-%d") if value else ""

	def handle_datetime_field(instance, field_name):
		value = getattr(instance, field_name)
		return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""

	def handle_time_field(instance, field_name):
		value = getattr(instance, field_name)
		return value.strftime("%H:%M:%S") if value else ""

	def handle_foreign_key_field(instance, field_name):
		field = model._meta.get_field(field_name)
		value = getattr(instance, field_name)
		response = {}
		if hasattr(value, 'dict') and callable(getattr(value, func_name)):
			response = getattr(value, func_name)()
		else:
			response = {"id": value.pk}
		return response

	def handle_many_to_many_field(instance, field_name):
		response = []
		many_related_manager = getattr(instance, field_name)
		related_instances = many_related_manager.all()
		for related_instance in related_instances:
			if hasattr(related_instance, 'dict') and callable(getattr(related_instance, func_name)):
				response.append(getattr(related_instance, func_name)())
			else:
				response.append({"id": related_instance.pk})
		return response

	def handle_file_field(instance, field_name):
		response = {}
		value = getattr(instance, field_name, None)
		if not value:
			return {}
		if hasattr(value, 'url'):
			response['url'] = value.url
		return response

	function_map = {
		DateField: handle_date_field,
		DateTimeField: handle_datetime_field,
		TimeField: handle_time_field,
		ForeignKey: handle_foreign_key_field,
		OneToOneField: handle_foreign_key_field,
		ManyToManyField: handle_many_to_many_field,
		ManyToOneRel: handle_many_to_many_field,
		FileField: handle_file_field,
		ImageField: handle_file_field,
	}

	for field_name in fields:
		field = model._meta.get_field(field_name)
		field_type = type(field)
		if field_type in function_map and callable(function_map[field_type]):
			response[field_name] = function_map[field_type](instance=instance, field_name=field_name)
		else:
			response[field_name] = str(getattr(instance, field_name))
	return response
