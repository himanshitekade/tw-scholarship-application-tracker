#REFER TO https://docs.djangoproject.com/en/4.1/howto/custom-template-tags/ FOR MORE UNDERSTANDING
#MAKE SURE THE FILTER NAMES ARE NOT IN CONFLICT WITH PRE-EXISTING TAGS CREATED BY YOU



from django import template
from django.template import Context

register = template.Library()

@register.simple_tag(name = 'isCheck')
def custom_for_check(value,arg1,arg2):	
	if arg2 in getattr(value,arg1):
		return True
	else:
		return False

@register.simple_tag(name = 'isRadio')
def custom_for_radio(value,arg1,arg2):
	if arg2 in getattr(value,arg1):
		return True
	else:
		return False

@register.filter(name="get")
def getValues(dict,key, default=''):
	value = getattr(dict,key["name"])
	
	if key["type"] == "file":
		return value.url
	elif key["name"] == "checkbox":
		print(value)
	return value
