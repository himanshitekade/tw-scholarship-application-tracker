from import_export import resources,fields
from .models import *
from openpyxl import load_workbook

class StSchFormDetailsResource(resources.ModelResource):
    class Meta:
        model = StSchFormDetails

class StLoanFormDetailsResource(resources.ModelResource):
    class Meta:
        model = StLoanFormDetails

class VachnalayaFormResource(resources.ModelResource):
    class Meta:
        model = VachnalayaForm

class SchoolFormResource(resources.ModelResource):
    class Meta:
        model = SchoolForm

class AnganwadiFormResource(resources.ModelResource):
    class Meta:
        model = AnganwadiForm

class InstitutionFormResource(resources.ModelResource):
    class Meta:
        model = InstitutionForm




