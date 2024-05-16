from .models import *


def privileges(request):
	print("privileges")
	if request.user.is_authenticated and not request.user.is_superuser:
		user_details = UserDetails.objects.get(user_id=request.user.id)
		privileges = []
		roles = []
		for role in user_details.role.all():
			roles.append(role.name)
			for privilege in role.privileges.all():
				privileges.append(privilege.name)
		
	else:
		privileges = []
		roles = []
	return {'privileges':privileges,'roles':roles} 


def reportsManagement(request):
	print("Entered REport context")
	if request.user.is_authenticated and not request.user.is_superuser:
		print("Entered Report context But should not")
		reports = ReportManagement.objects.filter(user=request.user).all()
		print(reports)
		if reports:
			return {"reports":reports}
		else:
			return {"reports":[]}

	else:
		return {"reports":[]}