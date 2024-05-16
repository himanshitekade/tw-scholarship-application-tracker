from django.urls import path
from sat_application import views
from .views import *

urlpatterns = [
    path('',UserLogin.as_view(), name='user-login'),
    path('signup',UserSignup.as_view(), name='user-signup'),
    path('stschformdetails/', views.StSchFormDetailsView.as_view(), name='stschformdetails'),
    path('stloanguarantorformdetails/', views.StLoanFormDetailsView.as_view(), 
        name='stloanguarantorformdetails'),
    path('applicantprofile', views.ApplicantProfileDetails.as_view(), name='applicantprofile'),
    path('vachanalayform/', views.VachnalayaFormView.as_view(), name='vachanalayform'),
    path('schoolform/', views.SchoolFormView.as_view(), name='schoolform'),
    path('anganwadiform/', views.AnganwadiFormView.as_view(), name='anganwadiform'),
    path('institutionform/', views.InstitutionFormView.as_view(), name='institutionform'),
    path('studentcategory/', views.StudentCategoryView.as_view(), name='studentcategory'),
    #APIs
    path('loginapi/', LoginApi.as_view(), name='loginapi'),
    path('process_applications1/',ProcessApplications1.as_view(), name='process_applications1'),
    path('process_applications2/',ProcessApplications2.as_view(), name='process_applications2'),
    path('process_applications3/',ProcessApplications3.as_view(), name='process_applications3'),
    path('uncategory_applications/',UncategoryApplications.as_view(), name='uncategory_applications'),
    path('view_application/',ViewApplication.as_view(), name='view_application'),
    path('dashboard/',Dashboard.as_view(), name='dashboard'),
    path('report-data-table/<int:id>',ReportQuery.as_view(),name='report-data-table'),
    path('view_process_applications1/',ViewProcessApplications1.as_view(), name='view_process_applications1'),
    path('view_process_applications2/',ViewProcessApplications2.as_view(), name='view_process_applications2'),
    path('view_process_applications3/',ViewProcessApplications3.as_view(), name='view_process_applications3'),

]