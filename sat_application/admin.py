from django.contrib import admin
from django.utils import timezone
from .models import *
from django.contrib.admin.models import LogEntry
from django.utils.html import format_html
from django.forms import CheckboxSelectMultiple

from import_export.admin import ImportExportModelAdmin
from .resources import *
from import_export.admin import ImportExportModelAdmin, ExportMixin
from import_export.formats import base_formats
from openpyxl import load_workbook


class UserDetailsAdmin(admin.ModelAdmin):
    model = UserDetails

    def save_model(self, request, obj, form, change):
        
        if obj.created_by: 
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id
      
        super().save_model(request, obj, form, change)
    
    formfield_overrides = {
            models.ManyToManyField: {'widget': CheckboxSelectMultiple},
        }

    list_display = ('username','created_By', 'created_at', 'updated_By', 'updated_at')

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

    def username(self,obj):

        return obj.user.username


admin.site.register(UserDetails, UserDetailsAdmin)
class RolesAdmin(admin.ModelAdmin):
    model = Roles

    def save_model(self, request, obj, form, change):
        
        if obj.created_by: 
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id
      
        super().save_model(request, obj, form, change)
    
    list_display = ('name','created_By', 'created_at', 'updated_By', 'updated_at')

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(Roles, RolesAdmin)



class PrivilegesAdmin(admin.ModelAdmin):
    model = Privileges

    def save_model(self, request, obj, form, change):
        
        if obj.created_by: 
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id
      
        super().save_model(request, obj, form, change)
    
    list_display = ('name','created_By', 'created_at', 'updated_By', 'updated_at')

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(Privileges, PrivilegesAdmin)


class TypeMasterAdmin(admin.ModelAdmin):
    model = TypeMaster

    def save_model(self, request, obj, form, change):
        
        if obj.created_by: 
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id
      
        super().save_model(request, obj, form, change)
    
    list_display = ('name','created_By', 'created_at', 'updated_By', 'updated_at')

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(TypeMaster, TypeMasterAdmin)


# class schSessionAdmin(admin.ModelAdmin):
#     model = schSession

#     def save_model(self, request, obj, form, change):
#         if obj.created_by:
#             obj.updated_by_id = request.user.id
#         else:
#             obj.created_by_id = request.user.id

#         super().save_model(request, obj, form, change)

#     list_display = ['year','start_session','end_session']

#     def created_By(self,obj):
#         if obj.created_by != None:
#             return obj.created_by.username

#     def updated_By(self,obj):
#         if obj.updated_by != None:
#             return obj.updated_by.username

class schSessionAdmin(admin.ModelAdmin):
    model = schSession
    list_display = ['year', 'start_session', 'end_session']

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(schSession,schSessionAdmin)


class StSchFormDetailsAdmin(ImportExportModelAdmin):
    model = StSchFormDetails

    def save_model(self, request, obj, form, change):
        if obj.created_by:
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id

        super().save_model(request, obj, form, change)

    list_display = ['email', 'first_name', 'last_name','created_By', 'created_at', 'updated_By', 'updated_at']

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(StSchFormDetails,StSchFormDetailsAdmin)


class StLoanFormDetailsAdmin(ImportExportModelAdmin):
    model = StLoanFormDetails

    def save_model(self, request, obj, form, change):
        if obj.created_by:
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id

        super().save_model(request, obj, form, change)

    list_display = ['email', 'first_name', 'last_name','created_By', 'created_at', 'updated_By', 'updated_at']

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(StLoanFormDetails,StLoanFormDetailsAdmin)


class StudentCategoryAdmin(admin.ModelAdmin):
    model = StudentCategory

    def save_model(self, request, obj, form, change):
        if obj.created_by:
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id

        super().save_model(request, obj, form, change)

    list_display = ['category_name', 'application_type','created_By', 'created_at', 'updated_By', 'updated_at']

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(StudentCategory,StudentCategoryAdmin)


class VachnalayaFormAdmin(ImportExportModelAdmin):
    model = VachnalayaForm

    def save_model(self, request, obj, form, change):
        if obj.created_by:
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id

        super().save_model(request, obj, form, change)

    list_display = ['email', 'name', 'created_By', 'created_at', 'updated_By', 'updated_at']

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(VachnalayaForm,VachnalayaFormAdmin)


class SchoolFormAdmin(ImportExportModelAdmin):
    model = SchoolForm

    def save_model(self, request, obj, form, change):
        if obj.created_by:
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id

        super().save_model(request, obj, form, change)

    list_display = ['email', 'name', 'created_By', 'created_at', 'updated_By', 'updated_at']

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(SchoolForm,SchoolFormAdmin)


class AnganwadiFormAdmin(ImportExportModelAdmin):
    model = AnganwadiForm

    def save_model(self, request, obj, form, change):
        if obj.created_by:
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id

        super().save_model(request, obj, form, change)

    list_display = ['email', 'name', 'created_By', 'created_at', 'updated_By', 'updated_at']

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(AnganwadiForm,AnganwadiFormAdmin)

class InstitutionFormAdmin(ImportExportModelAdmin):
    model = InstitutionForm

    def save_model(self, request, obj, form, change):
        if obj.created_by:
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id

        super().save_model(request, obj, form, change)
    list_display = ['email', 'name', 'created_By', 'created_at', 'updated_By', 'updated_at']

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(InstitutionForm,InstitutionFormAdmin)


class StSchFormDetailsDraftAdmin(admin.ModelAdmin):
    model = StSchFormDetailsDraft

    def save_model(self, request, obj, form, change):
        if obj.created_by:
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id

        super().save_model(request, obj, form, change)

    list_display = ['email', 'first_name', 'last_name','created_By', 'created_at', 'updated_By', 'updated_at']

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(StSchFormDetailsDraft,StSchFormDetailsDraftAdmin)


class StLoanFormDetailsDraftAdmin(admin.ModelAdmin):
    model = StLoanFormDetailsDraft

    def save_model(self, request, obj, form, change):
        if obj.created_by:
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id

        super().save_model(request, obj, form, change)

    list_display = ['email', 'first_name', 'last_name', 'created_By', 'created_at', 'updated_By', 'updated_at']

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(StLoanFormDetailsDraft,StLoanFormDetailsDraftAdmin)


class VachnalayaFormDraftAdmin(admin.ModelAdmin):
    model = VachnalayaFormDraft

    def save_model(self, request, obj, form, change):
        if obj.created_by:
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id

        super().save_model(request, obj, form, change)

    list_display = ['email', 'name', 'created_By', 'created_at', 'updated_By', 'updated_at']

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(VachnalayaFormDraft,VachnalayaFormDraftAdmin)


class SchoolFormDraftAdmin(admin.ModelAdmin):
    model = SchoolFormDraft

    def save_model(self, request, obj, form, change):
        if obj.created_by:
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id

        super().save_model(request, obj, form, change)

    list_display = ['email', 'name', 'created_By', 'created_at', 'updated_By', 'updated_at']

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(SchoolFormDraft,SchoolFormDraftAdmin)


class AnganwadiDraftAdmin(admin.ModelAdmin):
    model = AnganwadiFormDraft

    def save_model(self, request, obj, form, change):
        if obj.created_by:
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id

        super().save_model(request, obj, form, change)

    list_display = ['email', 'name', 'created_By', 'created_at', 'updated_By', 'updated_at']

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(AnganwadiFormDraft,AnganwadiDraftAdmin)


class InstitutionDraftAdmin(admin.ModelAdmin):
    model = InstitutionFormDraft

    def save_model(self, request, obj, form, change):
        if obj.created_by:
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id

        super().save_model(request, obj, form, change)

    list_display = ['email', 'name', 'created_By', 'created_at', 'updated_By', 'updated_at']

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username

admin.site.register(InstitutionFormDraft,InstitutionDraftAdmin)


class ReportManagementAdmin(admin.ModelAdmin):
    model = ReportManagement

    def save_model(self, request, obj, form, change):
        
        if obj.created_by: 
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id

        super().save_model(request, obj, form, change)
    
    list_display = ('name','query','created_By', 'created_at', 'updated_By', 'updated_at')

    formfield_overrides = {
            models.ManyToManyField: {'widget': CheckboxSelectMultiple},
        }

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username
        
admin.site.register(ReportManagement, ReportManagementAdmin)


class ReportFiltersAdmin(admin.ModelAdmin):
    model = ReportFilters

    def save_model(self, request, obj, form, change):
        
        if obj.created_by: 
            obj.updated_by_id = request.user.id
        else:
            obj.created_by_id = request.user.id

        super().save_model(request, obj, form, change)
    

    formfield_overrides = {
            models.ManyToManyField: {'widget': CheckboxSelectMultiple},
        }

    def created_By(self,obj):
        if obj.created_by != None:
            return obj.created_by.username

    def updated_By(self,obj):
        if obj.updated_by != None:
            return obj.updated_by.username


# Bulk Upload
# @admin.register(CrmForms)
# class CrmFormsAdmin(ImportExportModelAdmin):
#     list_display = ['companyName','tags']