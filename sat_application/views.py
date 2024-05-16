from django.shortcuts import render, redirect
from django.http import HttpResponse,Http404,JsonResponse,FileResponse
from django.views import View
from pytz import timezone 
from datetime import datetime
# from models import *
from sat_application.models import *
from .validate import * 
from datetime import datetime, timedelta,timezone
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
import json
import os
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import authenticate,login
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from phonenumber_field.phonenumber import PhoneNumber
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from decouple import config
from django.db import connection
from .utilities import *

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.apps import apps 
from django.db.models import Q
from openpyxl import Workbook
from django.db.models import Sum
from django.utils.safestring import mark_safe
from itertools import chain


# created_updated by function
def created_updated(model, request):
    user = request.user
    obj = model.objects.latest('pk')
    obj.created_by_id = request.user.id
    print("request.user.id", request.user.id)
    obj.save()
    obj.updated_by_id = request.user.id
    obj.save()


# UserLogin(# user login using email only)
class UserLogin(View):
    def get(self,request, *args, **kwargs):
        return render(request,'login.html')

    def post(self,request, *args, **kwargs):
        email = request.POST.get('email',None)
        password = request.POST.get('password',None)
        
        user = authenticate(request,email=email,password=password)
        if user is not None:
            user_details = UserDetails.objects.get(user_id=user.id)
            roles = Roles.objects.get(name='Organization Vachanalay')
            login(request,user)
            for i in user_details.role.all():
                print("role")
                return redirect('applicantprofile')
        else:
            return redirect('user-login')


#UserSignup
class UserSignup(View):
    def get(self,request, *args, **kwargs):

        roles = Roles.objects.filter(status_code=1).all().exclude(name__in=["Admin","Super Admin"])
        print("roles", roles)
        context = {"roles": roles}
        return render(request,'signup.html',context)

    def post(self,request, *args, **kwargs):
        validators = [UserAttributeSimilarityValidator,MinimumLengthValidator, NumericPasswordValidator]
        
        filled_data = dict(request.POST)
        filled_data.pop('csrfmiddlewaretoken')
        
        first_name = request.POST.get('first_name',None)
        last_name = request.POST.get('last_name',None)
        username = request.POST.get('username', None)
        email = request.POST.get('email', None)
        mobile = request.POST.get('mobile',None)
        password = request.POST.get('password1', None)
        conform_pwd = request.POST.get('password2', None)
        role = request.POST.getlist('role')

        roles = Roles.objects.filter(status_code=1).all().exclude(name__in=["Admin","Super Admin"])


        filled_data_roles = Roles.objects.filter(status_code=1,id__in=filled_data["role"]).all()

        if password != conform_pwd:
            context = {
                "filled_data":filled_data,
                "roles":roles,
                "filled_data_roles":filled_data_roles,
            }
            messages.error(request, ('Password and Confirm Password does not match'))
            return render(request, 'signup.html', context)
        else:
            try:
                for validator in validators:
                    if validator == UserAttributeSimilarityValidator:
                        user_attributes_array = (email)
                        er = validator().validate(password, user_attributes_array)
                    else:
                        er = validator().validate(password)
            except ValidationError as e:
                messages.error(request, str(e.message))
                context = {
                    "filled_data":filled_data,
                    "roles":roles,
                    "filled_data_roles":filled_data_roles,
                }
                return render(request, 'signup.html', context)

            hashed_pwd = make_password(conform_pwd)
            print("hashed_pwd", hashed_pwd)

            check_email = User.objects.filter(email=email).exists()
            if check_email:
                messages.error(request, ("User with this email already exist's, please try again with new one."))
                context = {
                    "filled_data":filled_data,
                    "roles":roles,
                    "filled_data_roles":filled_data_roles,
                    }
                return render(request, 'signup.html',context)
            else:
                try:
                    user = User(username=username, email=email,first_name=first_name, last_name=last_name, password=hashed_pwd)
                    user.save()
                    user_details = UserDetails(user_id=user.id, mobile=mobile)
                    user_details.save()

                    for id in request.POST.getlist('role'):
                        user_details.role.add(int(id))

                    if user:
                        messages.success(request, ("Account Created Successfully"))
                        return redirect('user-login')
                except Exception as ex:
                    messages.error(request, (ex))
                    context = {
                        "filled_data":filled_data,
                        "roles":roles,
                    }
                    return render(request, 'signup.html',context)


# APIs
@method_decorator(csrf_exempt, name='dispatch')
class LoginApi(View):
    def post(self,request,*args, **kwargs):
        email = request.headers.get('email', None)
        password = request.headers.get('password', None)
        user = authenticate(request, email=email, password=password)
        
        if user is not None:            
            try:
                user_data = UserDetails.objects.get(user_id=user.id)
                privileges=[]
                roles =[]
                for role in user_data.role.all():
                    roles.append(role.name)
                    for privilege in role.privileges.all():
                        privileges.append(privilege.name)
                    
                res = [*set(privileges)]
                data = []
                user_details = {
                "id":user.id,
                "first_name":user_data.user.first_name,
                "last_name":user_data.user.last_name,
                "email":user_data.user.email,
                "role":roles,
                "privileges":res,
                "mobile":str(user_data.mobile),
                }
                
                data.append(user_details)

                print(data)

                return JsonResponse({"userdetails":data},safe =False)

            except Exception as ex:

                return JsonResponse({"userdetails":str(ex),"messages":""})
        else:
            return JsonResponse({"userdetails":"","messages":"Incorrect username or password"},status=status.HTTP_404_NOT_FOUND)



#StSchFormDetailsView
@method_decorator(login_required, name='dispatch')
class StSchFormDetailsView(View):

    def get(self,request,*args, **kwargs):

        action = request.GET.get('action',None)

        # Fetch data from typemaster 
        talukas = TypeMaster.objects.filter(category = "type_taluka").all()
        districts = TypeMaster.objects.filter(category = "type_district").all()
        current_education_type = TypeMaster.objects.filter(category = "current_education_type").order_by('sequence')
        passed_education_type = TypeMaster.objects.filter(category = "passed_education_type").order_by('sequence')

        # Loading district in sch form
        if action == 'district':
            parent_id   = request.GET.get('parent_id',None)
            if parent_id:
                district_data = list(TypeMaster.objects.filter(parent_id=int(parent_id),display_flag=1).values("name"))
                return JsonResponse(district_data, safe=False)

        # Get current year id from session.
        current_year_id = schSession.objects.get(is_default = True)
        #  Get submitted and saved form status for current year.
        submitted_form = StSchFormDetails.objects.filter(email = request.user.email,sch_session_id= current_year_id.id).exists()
        saved_form = StSchFormDetailsDraft.objects.filter(email = request.user.email,sch_session_id= current_year_id.id).exists()
        loan_submitted_form = StLoanFormDetails.objects.filter(email = request.user.email,sch_session_id= current_year_id.id).exists()

        session_data = schSession.objects.all()
        user_data = UserDetails.objects.get(user_id=request.user.id)



        if submitted_form:
            return render(request, "scholarship_one_timeform_succesfully.html")

        elif loan_submitted_form:
            return render(request, "loan_one_timeform_succesfully.html")
           
        elif saved_form:
            form_saved_data = StSchFormDetailsDraft.objects.get(email = request.user.email,sch_session_id= current_year_id.id)
            selected_district_name = TypeMaster.objects.get(id=form_saved_data.district) if TypeMaster.objects.filter(id=form_saved_data.district).exists() else ""
            # selected_taluka_name = TypeMaster.objects.get(id = form_saved_data.taluka)  if TypeMaster.objects.filter(id=form_saved_data.taluka if form_saved_data.taluka != "" else 0).exists() else ""
            district_id = form_saved_data.district
            if district_id != "" and district_id != None:
                talukas = TypeMaster.objects.filter(category = "type_taluka",parent_id = district_id).all()

            context = {
                    
                    "talukas":talukas,
                    "districts":districts,
                    "current_education_type": current_education_type,
                    "passed_education_type":passed_education_type,

                    "form_saved_data":form_saved_data,
                    "selected_district_name":selected_district_name,
                    # "selected_taluka_name":selected_taluka_name,
                    
                    "session_data":session_data,
                    "user_data":user_data,
                    "District_id":int(form_saved_data.district) if (form_saved_data.district) != None else 0,
                    "current_year_id":current_year_id

                }
               
            return render(request,"create_student_scholarship_details_form.html",context)

        else:
            
            context = {
                    'session_data':session_data,
                    "talukas":talukas,
                    "districts":districts,
                    "current_education_type":current_education_type,
                    "passed_education_type":passed_education_type,
                    "user_data":user_data,
                    "current_year_id":current_year_id
                }

            return render(request, 'create_student_scholarship_details_form.html', context)
            
    # Create
    def post(self,request,*args, **kwargs):
       
        action = request.POST.get('action',None)

        first_name = request.POST.get('first_name', None)
        middle_name = request.POST.get('middle_name', None)
        last_name = request.POST.get('last_name', None)
        first_name_marathi = request.POST.get('first_name_marathi', None)
        middle_name_marathi = request.POST.get('middle_name_marathi', None)
        last_name_marathi = request.POST.get('last_name_marathi', None)
        address = request.POST.get('address', None)
        pincode = request.POST.get('pincode', None)
        email = request.POST.get('email', None)
        mobile = request.POST.get('mobile', None)
        district = request.POST.get('district', None)
        taluka = request.POST.get('taluka', None)
        mulgaon = request.POST.get('mulgaon', None)
        aadhar_card = request.FILES.get('aadhar_card', None)
        address_proof = request.FILES.get('address_proof', None)
        income_certificate = request.FILES.get('income_certificate', None)
        bonafide_certificate = request.FILES.get('bonafide_certificate', None)
        ration_card = request.FILES.get('ration_card', None)
        is_disablity_candidate = request.POST.get('is_disablity_candidate', None)
        disablity_certificate = request.FILES.get('disablity_certificate',None)
        passed_college_name = request.POST.get('passed_college_name', None)
        passed_education = request.POST.get('passed_education', None)
        passed_education_percentage = request.POST.get('passed_education_percentage', None)
        passed_education_marksheet = request.FILES.get('passed_education_marksheet',None)
        current_education = request.POST.get('current_education', None)
        is_application_received_previously = request.POST.get('is_application_received_previously', None)
        college_distance = request.POST.get('college_distance', None)
        college_travel_vehical = request.POST.get('college_travel_vehical', None)
        college_expenditure_tohome = request.POST.get('college_expenditure_tohome', None)
        family_details = request.POST.get('family_details', None)
        family_income = request.POST.get('family_income', None)
        tuition_fee = request.POST.get('tuition_fee', None)
        cost_books = request.POST.get('cost_books', None)
        cost_uniform = request.POST.get('cost_uniform', None)
        academic_year_cost_travel = request.POST.get('academic_year_cost_travel', None)
        hostel_fees = request.POST.get('hostel_fees', None)
        is_birth_place_different = request.POST.get('is_birth_place_different', None)
        birth_place = request.POST.get('birth_place', None)
        is_certificate_sports = request.POST.get('is_certificate_sports', None)
        upload_certificate_sports = request.FILES.get('upload_certificate_sports', None)
        is_alive = request.POST.get('is_alive', None)
        upload_certificate_isalive = request.FILES.get('upload_certificate_isalive', None)
        is_district_level_player = request.POST.get('is_district_level_player', None)
        upload_certificate_district_level = request.FILES.get('upload_certificate_district_level', None)
        bank_name = request.POST.get('bank_name', None)
        account_no = request.POST.get('account_no', None)
        account_holder = request.POST.get('account_holder', None)
        branch_name = request.POST.get('branch_name', None)
        ifsc_code = request.POST.get('ifsc_code', None)
        other_passed_education = request.POST.get('other_passed_Education', None)
        other_current_education = request.POST.get('other_current_education', None)
        other_taluka = request.POST.get('other_taluka', None)
        other_district = request.POST.get('other_district', None)
        teacher_one = request.FILES.get('teacher_one',None)
        teacher_two = request.FILES.get('teacher_two',None)
        is_other_sch_received = request.POST.get('is_other_sch_received',None)
        other_sch_received_amt = request.POST.get('other_sch_received_amt',None)
        fee_receipt = request.FILES.get('fee_receipt',None)
        birth_other_taluka = request.POST.get('birth_other_taluka', None)
        birth_other_district = request.POST.get('birth_other_district', None)
        birth_other_mulgaon = request.POST.get('birth_other_mulgaon', None)
        is_poverty_line = request.POST.get('is_poverty_line', None)
        upload_certificate_poverty_line = request.FILES.get('upload_certificate_poverty_line',None)
        upload_parent_teacher_certificate = request.FILES.get('upload_parent_teacher_certificate',None)
        st_sch_session = request.POST.get('st_sch_form_session', None)
        st_sch_session = int(st_sch_session)
        

        application_type = "Student Scholarship Form"
        # current_education , st_sch_session 

        # test category start
        # student_scholarship_form_category = StudentCategory.objects.filter(status_code=1,application_type = application_type,student_category_session = st_sch_session)
        if StudentCategory.objects.filter(status_code=1,application_type = application_type,student_category_session = st_sch_session).exists():
            student_scholarship_form_category = StudentCategory.objects.filter(status_code=1,application_type = application_type,student_category_session = st_sch_session)

            new_courses_list = []
            student_session_id_list = []
            for course in student_scholarship_form_category:
                courses_link_list = str(course.courses_link[1:-1])
                new_list = courses_link_list.split(", ")

                selected_courses_link_list = []
                for i in new_list:
                    new_item = i[1:-1]
                    selected_courses_link_list.append(new_item)

                # new_courses_list.extend(selected_courses_link_list)
                if current_education in selected_courses_link_list:
                    student_session_id_list.append(int(course.id))
                    

            # student_category = StudentCategory.objects.get(id = student_session_id_list[-1])
            if len(student_session_id_list)>=1:
                student_category = int(student_session_id_list[-1])
            else:
                student_category = False
        else:
            student_category = False

        passed_education_percentage = float(passed_education_percentage) if passed_education_percentage != "" else float(00)

        id = request.POST.get('id',None)
        if id:
            retrieved_data = True
            saved_data = StSchFormDetailsDraft.objects.get(id = id)            
        else:
            retrieved_data = False

       
        #submit
        if action == "submit": 


            # created_updated(StSchFormDetails)

            data_draft,is_created = StSchFormDetailsDraft.objects.update_or_create(email = request.user.email,sch_session_id=st_sch_session,
                defaults = {
                        "first_name":first_name, "middle_name":middle_name, "last_name":last_name, 
                        "first_name_marathi":first_name_marathi, "middle_name_marathi":middle_name_marathi, 
                        "last_name_marathi":last_name_marathi, "address":address, "pincode":pincode, 
                        "mobile":mobile, "district":district, "taluka":taluka, 
                        "mulgaon":mulgaon, "is_disablity_candidate":is_disablity_candidate, 
                        "disablity_certificate":saved_data.disablity_certificate if ((disablity_certificate == None) and retrieved_data) else  disablity_certificate,
                        "aadhar_card":saved_data.aadhar_card if ((aadhar_card == None) and retrieved_data) else  aadhar_card, 
                        "address_proof":saved_data.address_proof if (address_proof == None and retrieved_data) else  address_proof,
                        "income_certificate":saved_data.income_certificate if (income_certificate == None and retrieved_data) else  income_certificate, 
                        "bonafide_certificate":saved_data.bonafide_certificate if (bonafide_certificate == None and retrieved_data) else  bonafide_certificate,
                        "draft_status" :False,"sch_session_id": st_sch_session,
                        "ration_card":saved_data.ration_card if (ration_card == None and retrieved_data) else  ration_card, 
                        "passed_college_name": passed_college_name, "passed_education":passed_education, 
                        "passed_education_percentage":passed_education_percentage, 
                        "passed_education_marksheet":saved_data.passed_education_marksheet if (passed_education_marksheet == None and retrieved_data) else  passed_education_marksheet, 
                        "current_education":current_education, "is_application_received_previously":is_application_received_previously, 
                        "college_distance":college_distance, "college_travel_vehical":college_travel_vehical, 
                        "college_expenditure_tohome":college_expenditure_tohome, 
                        "family_details":family_details, "family_income":family_income, "tuition_fee":tuition_fee, "cost_books":cost_books,
                        "cost_uniform":cost_uniform, "academic_year_cost_travel":academic_year_cost_travel, 
                        "hostel_fees":hostel_fees, "is_birth_place_different":is_birth_place_different, "birth_place":birth_place, "is_certificate_sports":is_certificate_sports, 
                        "upload_certificate_sports": saved_data.upload_certificate_sports if (upload_certificate_sports == None and retrieved_data) else  upload_certificate_sports, 
                        "is_alive":is_alive, 
                        "upload_certificate_isalive":saved_data.upload_certificate_isalive if (upload_certificate_isalive == None and retrieved_data) else  upload_certificate_isalive,
                        "is_district_level_player":is_district_level_player,
                        "upload_certificate_district_level":saved_data.upload_certificate_district_level if (upload_certificate_district_level == None and retrieved_data) else  upload_certificate_district_level, 
                        "bank_name":bank_name, "account_no":account_no, "account_holder":account_holder, "branch_name":branch_name, 
                        "ifsc_code":ifsc_code,
                        "teacher_one":saved_data.teacher_one if (teacher_one == None and retrieved_data) else  teacher_one,
                        "teacher_two":saved_data.teacher_two if (teacher_two == None and retrieved_data) else  teacher_two,
                        "other_passed_Education":other_passed_education, 
                        "other_current_education":other_current_education,
                        "other_taluka":other_taluka, 
                        "other_district":other_district,
                        "fee_receipt":saved_data.fee_receipt if (fee_receipt == None and retrieved_data) else  fee_receipt,
                        "upload_certificate_poverty_line":saved_data.upload_certificate_poverty_line if (upload_certificate_poverty_line == None and retrieved_data) else  upload_certificate_poverty_line,
                        "upload_parent_teacher_certificate":saved_data.upload_parent_teacher_certificate if (upload_parent_teacher_certificate == None and retrieved_data) else  upload_parent_teacher_certificate,
                        "birth_other_taluka":birth_other_taluka,"birth_other_district":birth_other_district,
                        "birth_other_mulgaon":birth_other_mulgaon,"is_poverty_line":is_poverty_line,
                        "is_other_sch_received":is_other_sch_received,"other_sch_received_amt":other_sch_received_amt if other_sch_received_amt != '' else 0,
                        "student_category_id" : int(student_category) if student_category else None,
                        "text_field_1":"Draft","text_field_2":"Draft","text_field_3":"Draft"})
                # created_updated(StSchFormDetailsDraft)

            data = StSchFormDetails.objects.create(first_name = data_draft.first_name, middle_name = data_draft.middle_name,
                last_name = data_draft.last_name, first_name_marathi = data_draft.first_name_marathi, 
                middle_name_marathi = data_draft.middle_name_marathi, last_name_marathi = data_draft.last_name_marathi, 
                address = data_draft.address, pincode = data_draft.pincode, email = data_draft.email, mobile = data_draft.mobile, 
                district = data_draft.district, taluka = data_draft.taluka, mulgaon = data_draft.mulgaon, aadhar_card = data_draft.aadhar_card, 
                address_proof =data_draft.address_proof,other_taluka=data_draft.other_taluka, other_district=data_draft.other_district,
                income_certificate =data_draft.income_certificate,
                bonafide_certificate = data_draft.bonafide_certificate,other_sch_received_amt=data_draft.other_sch_received_amt,
                ration_card = data_draft.ration_card,is_other_sch_received=data_draft.is_other_sch_received,
                is_disablity_candidate = data_draft.is_disablity_candidate, 
                disablity_certificate = data_draft.disablity_certificate,
                passed_college_name = data_draft.passed_college_name,
                passed_education = data_draft.passed_education, passed_education_percentage = data_draft.passed_education_percentage, 
                passed_education_marksheet = data_draft.passed_education_marksheet,
                current_education = data_draft.current_education, 
                is_application_received_previously = data_draft.is_application_received_previously,
                college_distance = data_draft.college_distance,college_travel_vehical=data_draft.college_travel_vehical,college_expenditure_tohome = data_draft.college_expenditure_tohome,
                family_details = data_draft.family_details,family_income = data_draft.family_income,tuition_fee = data_draft.tuition_fee,cost_books = data_draft.cost_books,
                cost_uniform = data_draft.cost_uniform,academic_year_cost_travel = data_draft.academic_year_cost_travel,hostel_fees = data_draft.hostel_fees,
                is_birth_place_different = data_draft.is_birth_place_different,birth_place = data_draft.birth_place,is_certificate_sports = data_draft.is_certificate_sports,
                upload_certificate_sports = data_draft.upload_certificate_sports,
                is_alive = data_draft.is_alive,upload_certificate_isalive = data_draft.upload_certificate_isalive,
                is_district_level_player = data_draft.is_district_level_player,upload_certificate_district_level = data_draft.upload_certificate_district_level,
                bank_name = data_draft.bank_name,account_no = data_draft.account_no,account_holder = data_draft.account_holder,branch_name = data_draft.branch_name,ifsc_code=data_draft.ifsc_code, 
                sch_session_id = st_sch_session,teacher_one=data_draft.teacher_one,teacher_two=data_draft.teacher_two,
                fee_receipt = data_draft.fee_receipt,birth_other_taluka = data_draft.birth_other_taluka,
                birth_other_district = data_draft.birth_other_district,birth_other_mulgaon = data_draft.birth_other_mulgaon,
                is_poverty_line = data_draft.is_poverty_line,upload_certificate_poverty_line = data_draft.upload_certificate_poverty_line,
                upload_parent_teacher_certificate= data_draft.upload_parent_teacher_certificate,
                student_category_id = student_category if student_category else None, other_passed_education=other_passed_education, other_current_education=other_current_education,
                text_field_1 = "Draft",text_field_2 = "Draft",text_field_3 = "Draft")
                # other_passed_education=other_passed_education, other_current_education=other_current_education,
                # other_taluka=other_taluka, other_district=other_district,)

            # data = StSchFormDetails.objects.create(first_name = first_name, middle_name = middle_name,
            #     last_name = last_name, first_name_marathi = first_name_marathi, 
            #     middle_name_marathi = middle_name_marathi, last_name_marathi = last_name_marathi, 
            #     address = address, pincode = pincode, email = email, mobile = mobile, 
            #     district = district, taluka = taluka, mulgaon = mulgaon, aadhar_card = saved_data.aadhar_card if ((aadhar_card == None) and retrieved_data) else  aadhar_card, 
            #     address_proof =saved_data.address_proof if (address_proof == None and retrieved_data) else  address_proof,
            #     income_certificate =saved_data.income_certificate if (income_certificate == None and retrieved_data) else  income_certificate,
            #     bonafide_certificate = saved_data.bonafide_certificate if (bonafide_certificate == None and retrieved_data) else  bonafide_certificate,
            #     ration_card = saved_data.ration_card if (ration_card == None and retrieved_data) else  ration_card,
            #     is_disablity_candidate = is_disablity_candidate, 
            #     disablity_certificate = saved_data.disablity_certificate if ((disablity_certificate == None) and retrieved_data) else  disablity_certificate,
            #     passed_college_name = passed_college_name,
            #     passed_education = passed_education, passed_education_percentage = float(passed_education_percentage), 
            #     passed_education_marksheet = saved_data.passed_education_marksheet if (passed_education_marksheet == None and retrieved_data) else  passed_education_marksheet,
            #     current_education = current_education, 
            #     is_application_received_previously = is_application_received_previously,
            #     college_distance = college_distance,college_travel_vehical=college_travel_vehical,college_expenditure_tohome = college_expenditure_tohome,
            #     family_details = family_details,family_income = family_income,tuition_fee = tuition_fee,cost_books = cost_books,
            #     cost_uniform = cost_uniform,academic_year_cost_travel = academic_year_cost_travel,hostel_fees = hostel_fees,
            #     is_birth_place_different = is_birth_place_different,birth_place = birth_place,is_certificate_sports = is_certificate_sports,
            #     upload_certificate_sports = saved_data.upload_certificate_sports if (upload_certificate_sports == None and retrieved_data) else  upload_certificate_sports,
            #     is_alive = is_alive,upload_certificate_isalive = saved_data.upload_certificate_isalive if (upload_certificate_isalive == None and retrieved_data) else  upload_certificate_isalive,
            #     is_district_level_player = is_district_level_player,upload_certificate_district_level = saved_data.upload_certificate_district_level if (upload_certificate_district_level == None and retrieved_data) else  upload_certificate_district_level,
            #     bank_name = bank_name,account_no = account_no,account_holder = account_holder,branch_name = branch_name,ifsc_code=ifsc_code, 
            #     sch_session_id = session_year,teacher_one=saved_data.teacher_one if (teacher_one == None and retrieved_data) else  teacher_one,
            #     teacher_two=saved_data.teacher_two if (teacher_two == None and retrieved_data) else  teacher_two,
            #     student_category_id = student_category if student_category else None)
            #     # other_passed_education=other_passed_education, other_current_education=other_current_education,
            #     # other_taluka=other_taluka, other_district=other_district,)

            created_updated(StSchFormDetails, request)
            if data:
                return render(request, "scholarship_form_submitted_succesfully.html")
            else:
                return HttpResponse("Data not submitted!")

        #save
        elif action == "save":
            data,is_created = StSchFormDetailsDraft.objects.update_or_create(email = request.user.email,sch_session_id=st_sch_session,
                defaults = {
                        "first_name":first_name, "middle_name":middle_name, "last_name":last_name, 
                        "first_name_marathi":first_name_marathi, "middle_name_marathi":middle_name_marathi, 
                        "last_name_marathi":last_name_marathi, "address":address, "pincode":pincode, 
                        "mobile":mobile, "district":district, "taluka":taluka, 
                        "mulgaon":mulgaon, "is_disablity_candidate":is_disablity_candidate, 
                        "disablity_certificate":saved_data.disablity_certificate if ((disablity_certificate == None) and retrieved_data) else  disablity_certificate,
                        "aadhar_card":saved_data.aadhar_card if ((aadhar_card == None) and retrieved_data) else  aadhar_card, 
                        "address_proof":saved_data.address_proof if (address_proof == None and retrieved_data) else  address_proof,
                        "income_certificate":saved_data.income_certificate if (income_certificate == None and retrieved_data) else  income_certificate, 
                        "bonafide_certificate":saved_data.bonafide_certificate if (bonafide_certificate == None and retrieved_data) else  bonafide_certificate,
                        "draft_status" :True,"sch_session_id": st_sch_session,
                        "ration_card":saved_data.ration_card if (ration_card == None and retrieved_data) else  ration_card, 
                        "passed_college_name": passed_college_name, "passed_education":passed_education, 
                        "passed_education_percentage":passed_education_percentage, 
                        "passed_education_marksheet":saved_data.passed_education_marksheet if (passed_education_marksheet == None and retrieved_data) else  passed_education_marksheet, 
                        "current_education":current_education, "is_application_received_previously":is_application_received_previously, 
                        "college_distance":college_distance, "college_travel_vehical":college_travel_vehical, 
                        "college_expenditure_tohome":college_expenditure_tohome, 
                        "family_details":family_details, "family_income":family_income, "tuition_fee":tuition_fee, "cost_books":cost_books,
                        "cost_uniform":cost_uniform, "academic_year_cost_travel":academic_year_cost_travel, 
                        "hostel_fees":hostel_fees, "is_birth_place_different":is_birth_place_different, "birth_place":birth_place, "is_certificate_sports":is_certificate_sports, 
                        "upload_certificate_sports": saved_data.upload_certificate_sports if (upload_certificate_sports == None and retrieved_data) else  upload_certificate_sports, 
                        "is_alive":is_alive, 
                        "upload_certificate_isalive":saved_data.upload_certificate_isalive if (upload_certificate_isalive == None and retrieved_data) else  upload_certificate_isalive,
                        "is_district_level_player":is_district_level_player,
                        "upload_certificate_district_level":saved_data.upload_certificate_district_level if (upload_certificate_district_level == None and retrieved_data) else  upload_certificate_district_level, 
                        "bank_name":bank_name, "account_no":account_no, "account_holder":account_holder, "branch_name":branch_name, 
                        "ifsc_code":ifsc_code,
                        "teacher_one":saved_data.teacher_one if (teacher_one == None and retrieved_data) else  teacher_one,
                        "teacher_two":saved_data.teacher_two if (teacher_two == None and retrieved_data) else  teacher_two,
                        "other_passed_Education":other_passed_education, 
                        "other_current_education":other_current_education,
                        "fee_receipt":saved_data.fee_receipt if (fee_receipt == None and retrieved_data) else  fee_receipt,
                        "upload_certificate_poverty_line":saved_data.upload_certificate_poverty_line if (upload_certificate_poverty_line == None and retrieved_data) else  upload_certificate_poverty_line,
                        "upload_parent_teacher_certificate":saved_data.upload_parent_teacher_certificate if (upload_parent_teacher_certificate == None and retrieved_data) else  upload_parent_teacher_certificate,
                        "birth_other_taluka":birth_other_taluka,"birth_other_district":birth_other_district,
                        "birth_other_mulgaon":birth_other_mulgaon,"is_poverty_line":is_poverty_line,
                        "other_taluka":other_taluka, 
                        "other_district":other_district,
                        "is_other_sch_received":is_other_sch_received,"other_sch_received_amt":other_sch_received_amt if other_sch_received_amt != '' else 0,
                        "student_category_id" : int(student_category) if student_category else None,
                        "text_field_1":"Draft","text_field_2":"Draft","text_field_3":"Draft"}) 
                    

            created_updated(StSchFormDetailsDraft, request)
            
            if data:
                return render(request,"scholarship_form_save_succesfully.html")
            else:
                return HttpResponse("Data not SAVED!")
                    
            
        else:
            return HttpResponse("No action found!")



#StLoanGuarantorFormDetailsView
@method_decorator(login_required, name='dispatch')
class StLoanFormDetailsView(View):

    def get(self,request,*args, **kwargs):

        action = request.GET.get('action',None)
          
        # Get data from typemaster 
        talukas = TypeMaster.objects.filter(category = "type_taluka").all()
        districts = TypeMaster.objects.filter(category = "type_district").all()
        current_education_type = TypeMaster.objects.filter(category = "current_education_type").order_by('sequence')
        passed_education_type = TypeMaster.objects.filter(category = "passed_education_type").order_by('sequence')

        session_data = schSession.objects.all()
        user_data = UserDetails.objects.get(user_id=request.user.id)

        # Loading district in loan form
        if action == 'district':
            parent_id   = request.GET.get('parent_id',None)
            if parent_id:
                district_data = list(TypeMaster.objects.filter(parent_id=int(parent_id),display_flag=1).values("name"))
                return JsonResponse(district_data, safe=False)

        # Get current year id from session.
        current_year_id = schSession.objects.get(is_default = True)
       
        #  Get submitted and saved form status for current year.
        submitted_form = StLoanFormDetails.objects.filter(email = request.user.email,sch_session_id= current_year_id.id).exists()
        saved_form = StLoanFormDetailsDraft.objects.filter(email = request.user.email,sch_session_id= current_year_id.id).exists()
        sch_submitted_form = StSchFormDetails.objects.filter(email = request.user.email,sch_session_id= current_year_id.id).exists()

        
        if submitted_form:
            return render(request, "loan_one_timeform_succesfully.html")

        elif sch_submitted_form:
            return render(request, "scholarship_one_timeform_succesfully.html")
           
        elif saved_form:
            form_saved_data = StLoanFormDetailsDraft.objects.get(email = request.user.email,sch_session_id= current_year_id.id)
            selected_district_name = TypeMaster.objects.get(id=form_saved_data.district) if TypeMaster.objects.filter(id=form_saved_data.district).exists() else ""
            district_id = form_saved_data.district
            if district_id != "" and district_id != None:
                talukas = TypeMaster.objects.filter(category = "type_taluka",parent_id = district_id).all()

            context = {
                    
                    "talukas":talukas,
                    "districts":districts,
                    "current_education_type": current_education_type,
                    "passed_education_type":passed_education_type,

                    "form_saved_data":form_saved_data,
                    "selected_district_name":selected_district_name,
                    
                    "session_data":session_data,
                    "user_data":user_data,
                    "District_id":int(form_saved_data.district) if (form_saved_data.district) != None else 0,
                    "current_year_id":current_year_id

                }
               
            return render(request,"create_loan_scholarship_details_form.html",context)


        else:
           
            context = {
                    'session_data':session_data,
                    "talukas":talukas,
                    "districts":districts,
                    "current_education_type":current_education_type,
                    "passed_education_type":passed_education_type,
                    "user_data":user_data,
                    "current_year_id":current_year_id
                }

            return render(request, 'create_loan_scholarship_details_form.html', context)

    # Create
    def post(self,request,*args, **kwargs):
       
        first_name = request.POST.get('first_name', None)
        middle_name = request.POST.get('middle_name', None)
        last_name = request.POST.get('last_name', None)
        first_name_marathi = request.POST.get('first_name_marathi', None)
        middle_name_marathi = request.POST.get('middle_name_marathi', None)
        last_name_marathi = request.POST.get('last_name_marathi', None)
        address = request.POST.get('address', None)
        pincode = request.POST.get('pincode', None)
        email = request.POST.get('email', None)
        mobile = request.POST.get('mobile', None)
        district = request.POST.get('district', None)
        taluka = request.POST.get('taluka', None)
        mulgaon = request.POST.get('mulgaon', '')
        aadhar_card = request.FILES.get('aadhar_card', None)
        print("aadhar_card",aadhar_card)
        address_proof = request.FILES.get('address_proof', None)
        print("address_proof",address_proof)
        income_certificate = request.FILES.get('income_certificate', None)
        print("income_certificate",income_certificate)
        bonafide_certificate = request.FILES.get('bonafide_certificate', None)
        print("bonafide_certificate",bonafide_certificate)
        ration_card = request.FILES.get('ration_card', None)
        print("ration_card",ration_card)
        is_disablity_candidate = request.POST.get('is_disablity_candidate', None)
        disablity_certificate = request.FILES.get('disablity_certificate',None)
        print("disablity_certificate",disablity_certificate)
        passed_college_name = request.POST.get('passed_college_name', None)
        passed_education = request.POST.get('passed_education', None)
        other_passed_education = request.POST.get('other_passed_Education', None)
        other_current_education = request.POST.get('other_current_education', None)
        passed_education_percentage = request.POST.get('passed_education_percentage', None)
        passed_education_marksheet = request.FILES.get('passed_education_marksheet',None)
        print("passed_education_marksheet",passed_education_marksheet)
        current_education = request.POST.get('current_education', None)
        is_application_received_previously = request.POST.get('is_application_received_previously', None)
        guarantor_certificate_one = request.FILES.get('guarantor_certificate_one',None)
        print("guarantor_certificate_one",guarantor_certificate_one)
        guarantor_name_one = request.POST.get('guarantor_name_one', None)
        guarantor_address_one = request.POST.get('guarantor_address_one', None)
        guarantor_mobile_one = request.POST.get('guarantor_mobile_one', None)
        guarantor_certificate_two = request.FILES.get('guarantor_certificate_two',None)
        print("guarantor_certificate_two",guarantor_certificate_two)
        guarantor_name_two = request.POST.get('guarantor_name_two', None)
        guarantor_address_two = request.POST.get('guarantor_address_two', None)
        guarantor_mobile_two = request.POST.get('guarantor_mobile_two', None)
        loan_amount = request.POST.get('loan_amount', None)
        self_declaration_form = request.FILES.get('self_declaration_form',None)
        print("self_declaration_form",self_declaration_form)
        is_loan_received = request.POST.get('is_loan_received', None)
        current_education_fee = request.POST.get('current_education_fee', None)
        loan_amount_willing = request.POST.get('loan_amount_willing', None)
        action = request.POST.get('action',None)
        st_sch_session = request.POST.get('st_sch_loan_session', None)
        college_distance = request.POST.get('college_distance', None)
        college_travel_vehical = request.POST.get('college_travel_vehical', None)
        college_expenditure_tohome = request.POST.get('college_expenditure_tohome', None)
        family_details = request.POST.get('family_details', None)
        family_details = str(family_details).strip()
        family_income = request.POST.get('family_income', None)
        family_income = str(family_income).strip()
        tuition_fee = request.POST.get('tuition_fee', None)
        cost_books = request.POST.get('cost_books', None)
        cost_uniform = request.POST.get('cost_uniform', None)
        academic_year_cost_travel = request.POST.get('academic_year_cost_travel', None)
        hostel_fees = request.POST.get('hostel_fees', None)
        is_birth_place_different = request.POST.get('is_birth_place_different', None)
        birth_place = request.POST.get('birth_place', None)
        is_certificate_sports = request.POST.get('is_certificate_sports', None)
        upload_certificate_sports = request.FILES.get('upload_certificate_sports', None)
        print("upload_certificate_sports",upload_certificate_sports)
        is_alive = request.POST.get('is_alive', None)
        upload_certificate_isalive = request.FILES.get('upload_certificate_isalive', None)
        print("upload_certificate_isalive",upload_certificate_isalive)
        is_district_level_player = request.POST.get('is_district_level_player', None)
        upload_certificate_district_level = request.FILES.get('upload_certificate_district_level', None)
        print("upload_certificate_district_level",upload_certificate_district_level)
        bank_name = request.POST.get('bank_name', None)
        account_no = request.POST.get('account_no', None)
        account_holder = request.POST.get('account_holder', None)
        branch_name = request.POST.get('branch_name', None)
        ifsc_code = request.POST.get('ifsc_code', None)
        teacher_one = request.FILES.get('teacher_one',None)
        print("teacher_one",teacher_one)
        teacher_two = request.FILES.get('teacher_two',None)
        print("teacher_two",teacher_two)
        other_taluka = request.POST.get('other_taluka', None)
        other_district = request.POST.get('other_district', None)
        is_other_sch_received = request.POST.get('is_other_sch_received',None)
        other_sch_received_amt = request.POST.get('other_sch_received_amt',None)
        fee_receipt = request.FILES.get('fee_receipt',None)
        birth_other_taluka = request.POST.get('birth_other_taluka', None)
        birth_other_district = request.POST.get('birth_other_district', None)
        birth_other_mulgaon = request.POST.get('birth_other_mulgaon', None)
        is_poverty_line = request.POST.get('is_poverty_line', None)
        upload_certificate_poverty_line = request.FILES.get('upload_certificate_poverty_line',None)
        upload_parent_teacher_certificate = request.FILES.get('upload_parent_teacher_certificate',None)
        st_sch_session = int(st_sch_session)

        passed_education_percentage = float(passed_education_percentage) if passed_education_percentage != "" else float(00)
        loan_amount = float(loan_amount) if loan_amount != "" else float(00)

        # getting id
        id  = request.POST.get('id', None)

        if id:
            retrieved_data = True
            saved_data = StLoanFormDetailsDraft.objects.get(id = id)            
        else:
            retrieved_data = False

        # test category start
        application_type = "Student Loan Form"
        # student_loan_form_category = StudentCategory.objects.filter(status_code=1,application_type = application_type,student_category_session = st_sch_session)
        new_courses_list = []
        student_session_id_list = []
        if StudentCategory.objects.filter(status_code=1,application_type = application_type,student_category_session = st_sch_session).exists():
            student_loan_form_category = StudentCategory.objects.filter(status_code=1,application_type = application_type,student_category_session = st_sch_session)

            for course in student_loan_form_category:
                courses_link_list = str(course.courses_link[1:-1])
                new_list = courses_link_list.split(", ")

                selected_courses_link_list = []
                for i in new_list:
                    new_item = i[1:-1]
                    selected_courses_link_list.append(new_item)

                # new_courses_list.extend(selected_courses_link_list)
                if current_education in selected_courses_link_list:
                    student_session_id_list.append(int(course.id))
                    
            # student_category = StudentCategory.objects.get(id = student_session_id_list[-1])
            if len(student_session_id_list)>=1:
                student_category = int(student_session_id_list[-1])
            else:
                student_category = False
        else:
            student_category = False
    
        # submit
        if action == "submit":

            data_draft,is_created = StLoanFormDetailsDraft.objects.update_or_create(email = request.user.email,sch_session_id=st_sch_session,
                defaults = {
                        "first_name":first_name, "middle_name":middle_name, "last_name":last_name, 
                        "first_name_marathi":first_name_marathi, "middle_name_marathi":middle_name_marathi, 
                        "last_name_marathi":last_name_marathi, "address":address, "pincode":pincode, 
                        "mobile":mobile, "district":district, "taluka":taluka, 
                        "mulgaon":mulgaon, "is_disablity_candidate":is_disablity_candidate, 
                        "disablity_certificate":saved_data.disablity_certificate if ((disablity_certificate == None) and retrieved_data) else  disablity_certificate,
                        "aadhar_card":saved_data.aadhar_card if ((aadhar_card == None) and retrieved_data) else  aadhar_card, 
                        "address_proof":saved_data.address_proof if (address_proof == None and retrieved_data) else  address_proof,
                        "income_certificate":saved_data.income_certificate if (income_certificate == None and retrieved_data) else  income_certificate, 
                        "bonafide_certificate":saved_data.bonafide_certificate if (bonafide_certificate == None and retrieved_data) else  bonafide_certificate,
                        "loan_draft_status" :False,"sch_session_id": st_sch_session,
                        "ration_card":saved_data.ration_card if (ration_card == None and retrieved_data) else  ration_card, 
                        "passed_college_name": passed_college_name, "passed_education":passed_education, 
                        "passed_education_percentage":passed_education_percentage, 
                        "passed_education_marksheet":saved_data.passed_education_marksheet if (passed_education_marksheet == None and retrieved_data) else  passed_education_marksheet, 
                        "current_education":current_education,
                        "is_application_received_previously":is_application_received_previously, 
                        "college_distance":college_distance, "college_travel_vehical":college_travel_vehical, 
                        "college_expenditure_tohome":college_expenditure_tohome, 
                        "family_details":family_details, "family_income":family_income, "tuition_fee":tuition_fee, "cost_books":cost_books,
                        "cost_uniform":cost_uniform, "academic_year_cost_travel":academic_year_cost_travel, 
                        "hostel_fees":hostel_fees, "is_birth_place_different":is_birth_place_different, "birth_place":birth_place, "is_certificate_sports":is_certificate_sports, 
                        "upload_certificate_sports": saved_data.upload_certificate_sports if (upload_certificate_sports == None and retrieved_data) else  upload_certificate_sports, 
                        "is_alive":is_alive, 
                        "upload_certificate_isalive":saved_data.upload_certificate_isalive if (upload_certificate_isalive == None and retrieved_data) else  upload_certificate_isalive,
                        "is_district_level_player":is_district_level_player,
                        "upload_certificate_district_level":saved_data.upload_certificate_district_level if (upload_certificate_district_level == None and retrieved_data) else  upload_certificate_district_level, 
                        "bank_name":bank_name, "account_no":account_no, "account_holder":account_holder, "branch_name":branch_name, 
                        "ifsc_code":ifsc_code, 
                        "teacher_one":saved_data.teacher_one if (teacher_one == None and retrieved_data) else  teacher_one,
                        "teacher_two":saved_data.teacher_two if (teacher_two == None and retrieved_data) else  teacher_two,
                        "other_passed_Education":other_passed_education, 
                        "other_current_education":other_current_education,
                        "other_taluka":other_taluka, 
                        "other_district":other_district,
                        "is_other_sch_received":is_other_sch_received,"other_sch_received_amt":other_sch_received_amt if other_sch_received_amt != '' else 0,
                        "is_loan_received":is_loan_received, "loan_amount" : loan_amount, 
                        "self_declaration_form": saved_data.self_declaration_form if (self_declaration_form == None and retrieved_data) else  self_declaration_form,
                         "current_education_fee":current_education_fee,
                        "loan_amount_willing":loan_amount_willing,
                        "guarantor_certificate_one":saved_data.guarantor_certificate_one if (guarantor_certificate_one == None and retrieved_data) else  guarantor_certificate_one,
                        "guarantor_name_one":guarantor_name_one,
                        "guarantor_address_one":guarantor_address_one, "guarantor_mobile_one":guarantor_mobile_one,
                        "guarantor_certificate_two":saved_data.guarantor_certificate_two if (guarantor_certificate_two == None and retrieved_data) else  guarantor_certificate_two,
                         "guarantor_name_two":guarantor_name_two,
                        "guarantor_address_two":guarantor_address_two, "guarantor_mobile_two":guarantor_mobile_two, 
                        "fee_receipt":saved_data.fee_receipt if (fee_receipt == None and retrieved_data) else  fee_receipt,
                        "upload_certificate_poverty_line":saved_data.upload_certificate_poverty_line if (upload_certificate_poverty_line == None and retrieved_data) else  upload_certificate_poverty_line,
                        "upload_parent_teacher_certificate":saved_data.upload_parent_teacher_certificate if (upload_parent_teacher_certificate == None and retrieved_data) else  upload_parent_teacher_certificate,
                        "birth_other_taluka":birth_other_taluka,"birth_other_district":birth_other_district,
                        "birth_other_mulgaon":birth_other_mulgaon,"is_poverty_line":is_poverty_line,
                        "student_category_id" : int(student_category) if student_category else None,
                        "text_field_1":"Draft","text_field_2":"Draft","text_field_3":"Draft"})
            
            data = StLoanFormDetails.objects.create(first_name = data_draft.first_name, middle_name = data_draft.middle_name,
                last_name = data_draft.last_name, first_name_marathi = data_draft.first_name_marathi, 
                middle_name_marathi = data_draft.middle_name_marathi, last_name_marathi = data_draft.last_name_marathi, 
                address = data_draft.address, pincode = data_draft.pincode, email = data_draft.email, mobile = data_draft.mobile, 
                district = data_draft.district, taluka = data_draft.taluka, mulgaon = data_draft.mulgaon, aadhar_card = data_draft.aadhar_card, 
                address_proof =data_draft.address_proof, 
                income_certificate =data_draft.income_certificate,
                bonafide_certificate = data_draft.bonafide_certificate,
                ration_card = data_draft.ration_card, is_disablity_candidate = data_draft.is_disablity_candidate, 
                disablity_certificate = data_draft.disablity_certificate,
                passed_college_name = data_draft.passed_college_name,
                passed_education = data_draft.passed_education, passed_education_percentage = data_draft.passed_education_percentage, 
                passed_education_marksheet = data_draft.passed_education_marksheet, current_education = data_draft.current_education, 
                is_application_received_previously = data_draft.is_application_received_previously,
                college_distance = data_draft.college_distance,college_travel_vehical=data_draft.college_travel_vehical,college_expenditure_tohome = data_draft.college_expenditure_tohome,
                family_details = data_draft.family_details,family_income = data_draft.family_income,tuition_fee = data_draft.tuition_fee,cost_books = data_draft.cost_books,
                cost_uniform = data_draft.cost_uniform,academic_year_cost_travel = data_draft.academic_year_cost_travel,hostel_fees = data_draft.hostel_fees,
                is_birth_place_different = data_draft.is_birth_place_different,birth_place = data_draft.birth_place,is_certificate_sports = data_draft.is_certificate_sports,
                upload_certificate_sports = data_draft.upload_certificate_sports,
                is_alive = data_draft.is_alive,upload_certificate_isalive = data_draft.upload_certificate_isalive,
                is_district_level_player = data_draft.is_district_level_player,upload_certificate_district_level = data_draft.upload_certificate_district_level,
                bank_name = data_draft.bank_name,account_no = data_draft.account_no,account_holder = data_draft.account_holder,branch_name = data_draft.branch_name,ifsc_code=data_draft.ifsc_code, 
                other_passed_education=other_passed_education, other_current_education=other_current_education,
                other_taluka=data_draft.other_taluka, other_district=data_draft.other_district, 
                # other_taluka=other_taluka, other_district=other_district, 
                is_other_sch_received = data_draft.is_other_sch_received,other_sch_received_amt=data_draft.other_sch_received_amt,
                sch_session_id = st_sch_session,
                is_loan_received=data_draft.is_loan_received, loan_amount= data_draft.loan_amount, 
                self_declaration_form= data_draft.self_declaration_form, current_education_fee=data_draft.current_education_fee,
                loan_amount_willing=data_draft.loan_amount_willing,guarantor_certificate_one=data_draft.guarantor_certificate_one,
                guarantor_name_one=data_draft.guarantor_name_one,
                guarantor_address_one=data_draft.guarantor_address_one, guarantor_mobile_one=data_draft.guarantor_mobile_one,
                guarantor_certificate_two=data_draft.guarantor_certificate_two, guarantor_name_two=data_draft.guarantor_name_two,
                guarantor_address_two=data_draft.guarantor_address_two, guarantor_mobile_two=data_draft.guarantor_mobile_two,
                teacher_one=data_draft.teacher_one,
                teacher_two=data_draft.teacher_two,
                fee_receipt = data_draft.fee_receipt,birth_other_taluka = data_draft.birth_other_taluka,
                birth_other_district = data_draft.birth_other_district,birth_other_mulgaon = data_draft.birth_other_mulgaon,
                is_poverty_line = data_draft.is_poverty_line,upload_certificate_poverty_line = data_draft.upload_certificate_poverty_line,
                upload_parent_teacher_certificate= data_draft.upload_parent_teacher_certificate,
                student_category = data_draft.student_category,text_field_1="Draft",text_field_2 = "Draft",text_field_3 = "Draft")
            print("Data created ",data.id)


            # data = StLoanFormDetails.objects.create(first_name = first_name, middle_name = middle_name,
            #     last_name = last_name, first_name_marathi = first_name_marathi, 
            #     middle_name_marathi = middle_name_marathi, last_name_marathi = last_name_marathi, 
            #     address = address, pincode = pincode, email = email, mobile = mobile, 
            #     district = district, taluka = taluka, mulgaon = mulgaon, aadhar_card = saved_data.aadhar_card if ((aadhar_card == None) and retrieved_data) else  aadhar_card, 
            #     address_proof =saved_data.address_proof if (address_proof == None and retrieved_data) else  address_proof,
            #     income_certificate =saved_data.income_certificate if (income_certificate == None and retrieved_data) else  income_certificate,
            #     bonafide_certificate = saved_data.bonafide_certificate if (bonafide_certificate == None and retrieved_data) else  bonafide_certificate,
            #     ration_card = saved_data.ration_card if (ration_card == None and retrieved_data) else  ration_card, is_disablity_candidate = is_disablity_candidate, 
            #     disablity_certificate = saved_data.disablity_certificate if ((disablity_certificate == None) and retrieved_data) else  disablity_certificate,
            #     passed_college_name = passed_college_name,
            #     passed_education = passed_education, passed_education_percentage = float(passed_education_percentage), 
            #     passed_education_marksheet = saved_data.passed_education_marksheet if (passed_education_marksheet == None and retrieved_data) else  passed_education_marksheet, current_education = current_education, 
            #     is_application_received_previously = is_application_received_previously,
            #     college_distance = college_distance,college_travel_vehical=college_travel_vehical,college_expenditure_tohome = college_expenditure_tohome,
            #     family_details = family_details,family_income = family_income,tuition_fee = tuition_fee,cost_books = cost_books,
            #     cost_uniform = cost_uniform,academic_year_cost_travel = academic_year_cost_travel,hostel_fees = hostel_fees,
            #     is_birth_place_different = is_birth_place_different,birth_place = birth_place,is_certificate_sports = is_certificate_sports,
            #     upload_certificate_sports = saved_data.upload_certificate_sports if (upload_certificate_sports == None and retrieved_data) else  upload_certificate_sports,
            #     is_alive = is_alive,upload_certificate_isalive = saved_data.upload_certificate_isalive if (upload_certificate_isalive == None and retrieved_data) else  upload_certificate_isalive,
            #     is_district_level_player = is_district_level_player,upload_certificate_district_level = saved_data.upload_certificate_district_level if (upload_certificate_district_level == None and retrieved_data) else  upload_certificate_district_level,
            #     bank_name = bank_name,account_no = account_no,account_holder = account_holder,branch_name = branch_name,ifsc_code=ifsc_code, 
            #     # other_passed_education=other_passed_education, other_current_education=other_current_education,
            #     # other_taluka=other_taluka, other_district=other_district, 
            #     sch_session_id = session_year.id,
            #     is_loan_received=is_loan_received, loan_amount= loan_amount, 
            #     self_declaration_form= saved_data.self_declaration_form if (self_declaration_form == None and retrieved_data) else  self_declaration_form, current_education_fee=current_education_fee,
            #     loan_amount_willing=loan_amount_willing,guarantor_certificate_one=saved_data.guarantor_certificate_one if (guarantor_certificate_one == None and retrieved_data) else  guarantor_certificate_one,
            #     guarantor_name_one=guarantor_name_one,
            #     guarantor_address_one=guarantor_address_one, guarantor_mobile_one=guarantor_mobile_one,
            #     guarantor_certificate_two=saved_data.guarantor_certificate_two if (guarantor_certificate_two == None and retrieved_data) else  guarantor_certificate_two, guarantor_name_two=guarantor_name_two,
            #     guarantor_address_two=guarantor_address_two, guarantor_mobile_two=guarantor_mobile_two,
            #     teacher_one=saved_data.teacher_one if (teacher_one == None and retrieved_data) else  teacher_one,
            #     teacher_two=saved_data.teacher_two if (teacher_two == None and retrieved_data) else  teacher_two,
            #     student_category_id = student_category if student_category else None)
            # print("Data created ",data.id)

            created_updated(StLoanFormDetails, request)

            if data_draft:
                return render(request, "scholarship_loan_form_submitted_succesfully.html")
            else:
                return HttpResponse("Data not submitted!")

        #save
        if action == "save":
            data,is_created = StLoanFormDetailsDraft.objects.update_or_create(email = request.user.email,sch_session_id=st_sch_session,
                defaults = {
                        "first_name":first_name, "middle_name":middle_name, "last_name":last_name, 
                        "first_name_marathi":first_name_marathi, "middle_name_marathi":middle_name_marathi, 
                        "last_name_marathi":last_name_marathi, "address":address, "pincode":pincode, 
                        "mobile":mobile, "district":district, "taluka":taluka, 
                        "mulgaon":mulgaon, "is_disablity_candidate":is_disablity_candidate, 
                        "disablity_certificate":saved_data.disablity_certificate if ((disablity_certificate == None) and retrieved_data) else  disablity_certificate,
                        "aadhar_card":saved_data.aadhar_card if ((aadhar_card == None) and retrieved_data) else  aadhar_card, 
                        "address_proof":saved_data.address_proof if (address_proof == None and retrieved_data) else  address_proof,
                        "income_certificate":saved_data.income_certificate if (income_certificate == None and retrieved_data) else  income_certificate, 
                        "bonafide_certificate":saved_data.bonafide_certificate if (bonafide_certificate == None and retrieved_data) else  bonafide_certificate,
                         "loan_draft_status" :True,"sch_session_id": st_sch_session,
                        "ration_card":saved_data.ration_card if (ration_card == None and retrieved_data) else  ration_card, 
                        "passed_college_name": passed_college_name, "passed_education":passed_education, 
                        "passed_education_percentage":passed_education_percentage, 
                        "passed_education_marksheet":saved_data.passed_education_marksheet if (passed_education_marksheet == None and retrieved_data) else  passed_education_marksheet, 
                        "current_education":current_education,
                        "is_application_received_previously":is_application_received_previously, 
                        "college_distance":college_distance, "college_travel_vehical":college_travel_vehical, 
                        "college_expenditure_tohome":college_expenditure_tohome, 
                        "family_details":family_details, "family_income":family_income, "tuition_fee":tuition_fee, "cost_books":cost_books,
                        "cost_uniform":cost_uniform, "academic_year_cost_travel":academic_year_cost_travel, 
                        "hostel_fees":hostel_fees, "is_birth_place_different":is_birth_place_different, "birth_place":birth_place, "is_certificate_sports":is_certificate_sports, 
                        "upload_certificate_sports": saved_data.upload_certificate_sports if (upload_certificate_sports == None and retrieved_data) else  upload_certificate_sports, 
                        "is_alive":is_alive, 
                        "upload_certificate_isalive":saved_data.upload_certificate_isalive if (upload_certificate_isalive == None and retrieved_data) else  upload_certificate_isalive,
                         "is_district_level_player":is_district_level_player,
                        "upload_certificate_district_level":saved_data.upload_certificate_district_level if (upload_certificate_district_level == None and retrieved_data) else  upload_certificate_district_level, 
                        "bank_name":bank_name, "account_no":account_no, "account_holder":account_holder, "branch_name":branch_name, 
                        "ifsc_code":ifsc_code, 
                        "teacher_one":saved_data.teacher_one if (teacher_one == None and retrieved_data) else  teacher_one,
                        "teacher_two":saved_data.teacher_two if (teacher_two == None and retrieved_data) else  teacher_two,
                        "other_passed_Education":other_passed_education, 
                        "other_current_education":other_current_education,
                        
                        # "other_current_education":other_current_education,
                        "other_taluka":other_taluka, 
                        "other_district":other_district,
                        "is_other_sch_received":is_other_sch_received,"other_sch_received_amt":other_sch_received_amt if other_sch_received_amt != '' else 0,
                        "is_loan_received":is_loan_received, "loan_amount" : loan_amount, 
                        "self_declaration_form": saved_data.self_declaration_form if (self_declaration_form == None and retrieved_data) else  self_declaration_form,
                         "current_education_fee":current_education_fee,
                        "loan_amount_willing":loan_amount_willing,
                        "guarantor_certificate_one":saved_data.guarantor_certificate_one if (guarantor_certificate_one == None and retrieved_data) else  guarantor_certificate_one,
                        "guarantor_name_one":guarantor_name_one,
                        "guarantor_address_one":guarantor_address_one, "guarantor_mobile_one":guarantor_mobile_one,
                        "guarantor_certificate_two":saved_data.guarantor_certificate_two if (guarantor_certificate_two == None and retrieved_data) else  guarantor_certificate_two,
                        "guarantor_name_two":guarantor_name_two,
                        "guarantor_address_two":guarantor_address_two, "guarantor_mobile_two":guarantor_mobile_two, 
                        "fee_receipt":saved_data.fee_receipt if (fee_receipt == None and retrieved_data) else  fee_receipt,
                        "upload_certificate_poverty_line":saved_data.upload_certificate_poverty_line if (upload_certificate_poverty_line == None and retrieved_data) else  upload_certificate_poverty_line,
                        "upload_parent_teacher_certificate":saved_data.upload_parent_teacher_certificate if (upload_parent_teacher_certificate == None and retrieved_data) else  upload_parent_teacher_certificate,
                        "birth_other_taluka":birth_other_taluka,"birth_other_district":birth_other_district,
                        "birth_other_mulgaon":birth_other_mulgaon,"is_poverty_line":is_poverty_line,
                        "student_category_id" : int(student_category) if student_category else None,
                        "text_field_1":"Draft","text_field_2":"Draft","text_field_3":"Draft"}) 
            
            created_updated(StLoanFormDetailsDraft, request)

            if data:
                return render(request,"scholarship_loan_form_save_succesfully.html")
            else:
                return HttpResponse("Data not SAVED!")
                    

#VachnalayaFormView
@method_decorator(login_required, name='dispatch')
class VachnalayaFormView(View):
    def get(self,request,*args, **kwargs):

        action = request.GET.get('action',None)

        # Fetch data from typemaster 
        talukas = TypeMaster.objects.filter(category = "type_taluka").all()
        districts = TypeMaster.objects.filter(category = "type_district").all()

        # Loading district in Vachanalay form
        if action == 'district':
            parent_id   = request.GET.get('parent_id',None)
            if parent_id:
                district_data = list(TypeMaster.objects.filter(parent_id=int(parent_id),display_flag=1).values("name"))
                return JsonResponse(district_data, safe=False)

        # Get current year id from session.
        current_year_id = schSession.objects.get(is_default = True)

        # Get submitted and saved form status for current year.
        vachanalay_submitted_form = VachnalayaForm.objects.filter(email = request.user.email,sch_session_id= current_year_id.id).exists()
        print("vachanalay_submitted_form", vachanalay_submitted_form)
        saved_form = VachnalayaFormDraft.objects.filter(email = request.user.email,sch_session_id= current_year_id.id).exists()


        session_data = schSession.objects.all()
        user_data = UserDetails.objects.get(user_id=request.user.id)
       
        if vachanalay_submitted_form:
            return render(request, "vachanalay_one_timeform_successfully.html")
           
        elif saved_form:
            form_saved_data = VachnalayaFormDraft.objects.get(email = request.user.email,sch_session_id= current_year_id.id)
            selected_district_name = TypeMaster.objects.get(id=form_saved_data.district) if TypeMaster.objects.filter(id=form_saved_data.district).exists() else ""
            district_id = form_saved_data.district
            if district_id != "" and district_id != None:
                talukas = TypeMaster.objects.filter(category = "type_taluka",parent_id = district_id).all()

            date_organization_started = form_saved_data.organization_started.strftime('%Y-%m-%d') if form_saved_data.organization_started else ''

            context = {
                    
                    "talukas":talukas,
                    "districts":districts,
                    "form_saved_data":form_saved_data,
                    "selected_district_name":selected_district_name,
                    "date_organization_started":date_organization_started ,
                    
                    "session_data":session_data,
                    "user_data":user_data,
                    "District_id":int(form_saved_data.district) if (form_saved_data.district) != None else 0,
                    "current_year_id":current_year_id
                }
               
            return render(request,"create_vachanalay_form.html",context)

        else:
            print("ENTERED IN ELSE")
            context = {
                    'session_data':session_data,
                    "talukas":talukas,
                    "districts":districts,
                    "user_data":user_data,
                    "current_year_id":current_year_id
                }

            return render(request,"create_vachanalay_form.html",context)


     # Create
    def post(self,request,*args, **kwargs):
        
        action = request.POST.get('action',None)


        name = request.POST.get('name', None)
        email = request.user.email
        address = request.POST.get('address', None)
        pincode = request.POST.get('pincode', None)
        authority_name = request.POST.get('authority_name', None)
        mobile = request.POST.get('mobile', None)
        landline_no = request.POST.get('landline_no', None)
        district = request.POST.get('district', None)
        taluka = request.POST.get('taluka', None)
        mulgaon = request.POST.get('mulgaon', ' ')
        organization_started = request.POST.get('organization_started', None)
        is_org_register = request.POST.get('is_org_register', None)
        org_register_certificate = request.FILES.get('org_register_certificate', None)
        bank_name = request.POST.get('bank_name', None)
        account_no = request.POST.get('account_no', None)
        account_holder = request.POST.get('account_holder', None)
        branch_name = request.POST.get('branch_name', None)
        ifsc_code = request.POST.get('ifsc_code', None)
        is_scholarship_recevied = request.POST.get('is_scholarship_recevied', None)
        cancelled_cheque = request.FILES.get('cancelled_cheque', None)
        student_book_count_first_year = request.POST.get('student_book_count_first_year', None)
        student_book_count_second_year = request.POST.get('student_book_count_second_year', None)
        student_book_count_third_year = request.POST.get('student_book_count_third_year', None)
        expenditure_first_year = request.POST.get('expenditure_first_year', None)
        expenditure_second_year = request.POST.get('expenditure_second_year', None)
        expenditure_third_year = request.POST.get('expenditure_third_year', None)
        details_source_income = request.POST.get('details_source_income', None)
        bank_statement_first_year = request.FILES.get('bank_statement_first_year', None)
        bank_statement_second_year = request.FILES.get('bank_statement_second_year', None)
        bank_statement_third_year = request.FILES.get('bank_statement_third_year', None)
        current_total_expenditure = request.POST.get('current_total_expenditure',None)
        student_count_current_year = request.POST.get('student_count_current_year',None)
        item_details_expense = request.POST.get('item_details_expense', None)
        employee_details = request.POST.get('employee_details', None)
        st_vachanalay_session = request.POST.get('vachanalay_form_session', None)
        other_taluka = request.POST.get('other_taluka', None)
        other_district = request.POST.get('other_district', None)
        st_vachanalay_session = int(st_vachanalay_session)
        
        # session_year = schSession.objects.get(id = st_vachanalay_session)
        application_type = "Vachnalaya Form"
        # Student Category ID
        # vachanalay_form_category = StudentCategory.objects.get(status_code=1,application_type = application_type,student_category_session = st_vachanalay_session)
        # student_category = vachanalay_form_category.id
        if StudentCategory.objects.filter(status_code=1,application_type = application_type,student_category_session = st_vachanalay_session).exists():
            vachanalay_form_category = StudentCategory.objects.get(status_code=1,application_type = application_type,student_category_session = st_vachanalay_session)
            student_category = vachanalay_form_category.id
        else:
            student_category = False

        id = request.POST.get('id',None)

        if id:
            retrieved_data = True
            saved_data = VachnalayaFormDraft.objects.get(id = id)            
        else:
            retrieved_data = False

        #submit
        if action == "submit":
            
            data_draft,is_created = VachnalayaFormDraft.objects.update_or_create(email = request.user.email,sch_session_id=st_vachanalay_session,
                defaults = {
                        "other_taluka":other_taluka, 
                        "other_district":other_district,
                        "name":name, "address":address, 
                        "pincode":pincode, "mobile":mobile, "landline_no":landline_no, "authority_name":authority_name,
                        "district":district, "taluka": taluka, "mulgaon":mulgaon, 
                        "organization_started":organization_started if organization_started != '' else None,
                        "is_org_register":is_org_register, "org_register_certificate":saved_data.org_register_certificate if 
                        ((org_register_certificate == None) and retrieved_data ) else org_register_certificate, 
                        "bank_name":bank_name,"account_no":account_no,"account_holder":account_holder,
                        "branch_name":branch_name,"ifsc_code":ifsc_code, "is_scholarship_recevied":is_scholarship_recevied,
                        "cancelled_cheque":saved_data.cancelled_cheque if 
                        ((cancelled_cheque == None) and retrieved_data ) else cancelled_cheque,
                        "student_book_count_first_year":student_book_count_first_year,
                        "student_book_count_second_year":student_book_count_second_year, 
                        "student_book_count_third_year":student_book_count_third_year, "expenditure_first_year":expenditure_first_year,
                        "expenditure_second_year":expenditure_second_year, "expenditure_third_year":expenditure_third_year,
                        "details_source_income":details_source_income, "item_details_expense":item_details_expense,
                        "employee_details":employee_details, "sch_session_id":st_vachanalay_session, 
                        "bank_statement_first_year":saved_data.bank_statement_first_year if 
                        ((bank_statement_first_year == None) and retrieved_data ) else bank_statement_first_year,
                        "bank_statement_second_year":saved_data.bank_statement_second_year if 
                        ((bank_statement_second_year == None) and retrieved_data ) else bank_statement_second_year,
                        "bank_statement_third_year":saved_data.bank_statement_third_year if 
                        ((bank_statement_third_year == None) and retrieved_data ) else bank_statement_third_year,
                        "current_total_expenditure":current_total_expenditure if current_total_expenditure != '' else 0,"student_count_current_year":student_count_current_year,
                        "vachanalay_form_status":False,
                        "student_category_id" : int(student_category) if student_category else None,
                        "text_field_1":"Draft","text_field_2":"Draft","text_field_3":"Draft"}) 

            data = VachnalayaForm.objects.create(name = data_draft.name, address = data_draft.address, email=data_draft.email,
                pincode = data_draft.pincode, mobile = data_draft.mobile, landline_no=data_draft.landline_no, authority_name=data_draft.authority_name,
                district = data_draft.district, taluka = data_draft.taluka, mulgaon = data_draft.mulgaon, organization_started=data_draft.organization_started,
                is_org_register= data_draft.is_org_register, org_register_certificate=data_draft.org_register_certificate, 
                bank_name = data_draft.bank_name,account_no = data_draft.account_no,account_holder = data_draft.account_holder,
                branch_name = data_draft.branch_name,ifsc_code=data_draft.ifsc_code, is_scholarship_recevied=data_draft.is_scholarship_recevied,
                cancelled_cheque=data_draft.cancelled_cheque,student_book_count_first_year=data_draft.student_book_count_first_year,
                student_book_count_second_year=data_draft.student_book_count_second_year, 
                student_book_count_third_year=data_draft.student_book_count_third_year, expenditure_first_year=data_draft.expenditure_first_year,
                expenditure_second_year=data_draft.expenditure_second_year, expenditure_third_year=data_draft.expenditure_third_year,
                details_source_income=data_draft.details_source_income, item_details_expense=data_draft.item_details_expense,
                employee_details=data_draft.employee_details, sch_session_id = st_vachanalay_session,
                bank_statement_first_year=data_draft.bank_statement_first_year,
                bank_statement_second_year=data_draft.bank_statement_second_year,
                bank_statement_third_year=data_draft.bank_statement_third_year,
                current_total_expenditure=current_total_expenditure,
                student_count_current_year=data_draft.student_count_current_year,
                other_taluka=data_draft.other_taluka, other_district=data_draft.other_district,
                student_category = data_draft.student_category,text_field_1 = "Draft",text_field_2 = "Draft",text_field_3 = "Draft"
                )

            # data = VachnalayaForm.objects.create(name = name, address = address, email=email,
            #     pincode = pincode, mobile = mobile, landline_no=landline_no, authority_name=authority_name,
            #     district = district, taluka = taluka, mulgaon = mulgaon, organization_started=organization_started,
            #     is_org_register= is_org_register, org_register_certificate=saved_data.org_register_certificate if 
            #     ((org_register_certificate == None) and retrieved_data ) else org_register_certificate, 
            #     bank_name = bank_name,account_no = account_no,account_holder = account_holder,
            #     branch_name = branch_name,ifsc_code=ifsc_code, is_scholarship_recevied=is_scholarship_recevied,
            #     cancelled_cheque=saved_data.cancelled_cheque if 
            #     ((cancelled_cheque == None) and retrieved_data ) else cancelled_cheque,student_book_count_first_year=student_book_count_first_year,
            #     student_book_count_second_year=student_book_count_second_year, 
            #     student_book_count_third_year=student_book_count_third_year, expenditure_first_year=expenditure_first_year,
            #     expenditure_second_year=expenditure_second_year, expenditure_third_year=expenditure_third_year,
            #     details_source_income=details_source_income, item_details_expense=item_details_expense,
            #     employee_details=employee_details, sch_session_id = int(st_vachanalay_session),
            #     bank_statement=saved_data.bank_statement if 
            #     ((bank_statement == None) and retrieved_data ) else bank_statement)

            created_updated(VachnalayaForm, request)

            if data:
                return render(request, "vachanalay_form_submitted_successfully.html")
            else:
                return HttpResponse("Data not submitted!")

        #save 
        elif action == "save":
            
            data,is_created = VachnalayaFormDraft.objects.update_or_create(email = request.user.email,sch_session_id=st_vachanalay_session,
                defaults = {
                        "other_taluka":other_taluka, 
                        "other_district":other_district,
                        "name":name, "address":address, 
                        "pincode":pincode, "mobile":mobile, "landline_no":landline_no, "authority_name":authority_name,
                        "district":district, "taluka": taluka, "mulgaon":mulgaon, 
                        "organization_started":organization_started if organization_started != '' else None,
                        "is_org_register":is_org_register, "org_register_certificate":saved_data.org_register_certificate if 
                        ((org_register_certificate == None) and retrieved_data ) else org_register_certificate, 
                        "bank_name":bank_name,"account_no":account_no,"account_holder":account_holder,
                        "branch_name":branch_name,"ifsc_code":ifsc_code, "is_scholarship_recevied":is_scholarship_recevied,
                        "cancelled_cheque":saved_data.cancelled_cheque if 
                        ((cancelled_cheque == None) and retrieved_data ) else cancelled_cheque,
                        "student_book_count_first_year":student_book_count_first_year,
                        "student_book_count_second_year":student_book_count_second_year, 
                        "student_book_count_third_year":student_book_count_third_year, "expenditure_first_year":expenditure_first_year,
                        "expenditure_second_year":expenditure_second_year, "expenditure_third_year":expenditure_third_year,
                        "details_source_income":details_source_income, "item_details_expense":item_details_expense,
                        "employee_details":employee_details, "sch_session_id":st_vachanalay_session, 
                        "bank_statement_first_year":saved_data.bank_statement_first_year if 
                        ((bank_statement_first_year == None) and retrieved_data ) else bank_statement_first_year,
                        "bank_statement_second_year":saved_data.bank_statement_second_year if 
                        ((bank_statement_second_year == None) and retrieved_data ) else bank_statement_second_year,
                        "bank_statement_third_year":saved_data.bank_statement_third_year if 
                        ((bank_statement_third_year == None) and retrieved_data ) else bank_statement_third_year,
                        "current_total_expenditure":current_total_expenditure if current_total_expenditure != '' else 0,"student_count_current_year":student_count_current_year,
                        "vachanalay_form_status":True,"student_category_id" : int(student_category) if student_category else None,
                        "text_field_1":"Draft","text_field_2":"Draft","text_field_3":"Draft"
                        }) 
            created_updated(VachnalayaFormDraft, request)

            if data:
                return render(request,"vachanalay_form_save_successfully.html")
            else:
                return HttpResponse("Data not SAVED!")
                    
            
        else:
            return HttpResponse("No action found!")


#SchoolFormView
@method_decorator(login_required, name='dispatch')
class SchoolFormView(View):

    def get(self,request,*args, **kwargs):
        
        action = request.GET.get('action',None)

        # Fetch data from typemaster 
        talukas = TypeMaster.objects.filter(category = "type_taluka").all()
        districts = TypeMaster.objects.filter(category = "type_district").all()

        # Loading district in School form
        if action == 'district':
            parent_id   = request.GET.get('parent_id',None)
            if parent_id:
                district_data = list(TypeMaster.objects.filter(parent_id=int(parent_id),display_flag=1).values("name"))
                return JsonResponse(district_data, safe=False)

        # Get current year id from session.
        current_year_id = schSession.objects.get(is_default = True)


        # Get submitted and saved form status for current year.
        school_submitted_form = SchoolForm.objects.filter(email = request.user.email,sch_session_id= current_year_id.id).exists()
        saved_form = SchoolFormDraft.objects.filter(email = request.user.email,sch_session_id= current_year_id.id).exists()


        session_data = schSession.objects.all()
        user_data = UserDetails.objects.get(user_id=request.user.id)
       
        if school_submitted_form:

            return render(request, "school_one_time_successfully.html")
           
        elif saved_form:
            form_saved_data = SchoolFormDraft.objects.get(email = request.user.email,sch_session_id= current_year_id.id)
            selected_district_name = TypeMaster.objects.get(id=form_saved_data.district) if TypeMaster.objects.filter(id=form_saved_data.district).exists() else ""
            district_id = form_saved_data.district
            if district_id != "" and district_id != None:
                talukas = TypeMaster.objects.filter(category = "type_taluka",parent_id = district_id).all()

            date_organization_started = form_saved_data.organization_started.strftime('%Y-%m-%d') if form_saved_data.organization_started else ''

            context = {
                    
                    "talukas":talukas,
                    "districts":districts,
                    "form_saved_data":form_saved_data,
                    "selected_district_name":selected_district_name,
                    "date_organization_started":date_organization_started,
                    "session_data":session_data,
                    "user_data":user_data,
                    "District_id":int(form_saved_data.district) if (form_saved_data.district) != None else 0,
                    "current_year_id":current_year_id

                }
               
            return render(request,"create_school_form.html",context)

        else:
        
            context = {
                    'session_data':session_data,
                    "talukas":talukas,
                    "districts":districts,
                    "user_data":user_data,
                    "current_year_id":current_year_id
                }

            return render(request,"create_school_form.html",context)

    def post(self,request,*args, **kwargs):

        action = request.POST.get('action',None)


        name = request.POST.get('name', None)
        email = request.user.email
        address = request.POST.get('address', None)
        pincode = request.POST.get('pincode', None)
        authority_name = request.POST.get('authority_name', None)
        mobile = request.POST.get('mobile', None)
        landline_no = request.POST.get('landline_no', None)
        district = request.POST.get('district', None)
        taluka = request.POST.get('taluka', None)
        mulgaon = request.POST.get('mulgaon', ' ')
        organization_started = request.POST.get('organization_started', None)
        is_org_register = request.POST.get('is_org_register', None)
        org_register_certificate = request.FILES.get('org_register_certificate', None)
        bank_name = request.POST.get('bank_name', None)
        account_no = request.POST.get('account_no', None)
        account_holder = request.POST.get('account_holder', None)
        branch_name = request.POST.get('branch_name', None)
        ifsc_code = request.POST.get('ifsc_code', None)
        is_scholarship_recevied = request.POST.get('is_scholarship_recevied', None)
        cancelled_cheque = request.FILES.get('cancelled_cheque', None)
        student_book_count_first_year = request.POST.get('student_book_count_first_year', None)
        student_book_count_second_year = request.POST.get('student_book_count_second_year', None)
        student_book_count_third_year = request.POST.get('student_book_count_third_year', None)
        expenditure_first_year = request.POST.get('expenditure_first_year', None)
        expenditure_second_year = request.POST.get('expenditure_second_year', None)
        expenditure_third_year = request.POST.get('expenditure_third_year', None)
        details_source_income = request.POST.get('details_source_income', None)
        bank_statement_first_year = request.FILES.get('bank_statement_first_year', None)
        bank_statement_second_year = request.FILES.get('bank_statement_second_year', None)
        bank_statement_third_year = request.FILES.get('bank_statement_third_year', None)
        current_total_expenditure = request.POST.get('current_total_expenditure',None)
        student_count_current_year = request.POST.get('student_count_current_year',None)
        item_details_expense = request.POST.get('item_details_expense', None)
        employee_details = request.POST.get('employee_details', None)
        school_form_session = request.POST.get('school_form_session', None)
        name_of_principal = request.POST.get('name_of_principal',None)
        other_taluka = request.POST.get('other_taluka', None)
        other_district = request.POST.get('other_district', None)
        school_form_session = int(school_form_session)
        print("school_form_session:-",school_form_session)
        
        application_type = "School Form"
        # Student Category ID
        # school_form_category = StudentCategory.objects.get(status_code=1,application_type = application_type,student_category_session = school_form_session)
        # student_category = school_form_category.id
        if StudentCategory.objects.filter(status_code=1,application_type = application_type,student_category_session = school_form_session).exists():
            school_form_category = StudentCategory.objects.get(status_code=1,application_type = application_type,student_category_session = school_form_session)
            student_category = school_form_category.id
        else:
            student_category = False




        id = request.POST.get('id',None)

        if id:
            retrieved_data = True
            saved_data = SchoolFormDraft.objects.get(id = id)            
        else:
            retrieved_data = False

        
        if action == "submit": 

            
            data_draft,is_created = SchoolFormDraft.objects.update_or_create(email = request.user.email,sch_session_id=school_form_session,
                defaults = {
                        "other_taluka":other_taluka, 
                        "other_district":other_district,
                        "name":name, "address":address, 
                        "pincode":pincode, "mobile":mobile, "landline_no":landline_no, "authority_name":authority_name,
                        "district":district, "taluka": taluka, "mulgaon":mulgaon, 
                        "organization_started":organization_started if organization_started != '' else None,
                        "is_org_register":is_org_register, "org_register_certificate":saved_data.org_register_certificate if 
                        ((org_register_certificate == None) and retrieved_data ) else org_register_certificate, 
                        "bank_name":bank_name,"account_no":account_no,"account_holder":account_holder,
                        "branch_name":branch_name,"ifsc_code":ifsc_code, "is_scholarship_recevied":is_scholarship_recevied,
                        "cancelled_cheque":saved_data.cancelled_cheque if 
                        ((cancelled_cheque == None) and retrieved_data ) else cancelled_cheque,
                        "student_book_count_first_year":student_book_count_first_year,
                        "student_book_count_second_year":student_book_count_second_year, 
                        "student_book_count_third_year":student_book_count_third_year, "expenditure_first_year":expenditure_first_year,
                        "expenditure_second_year":expenditure_second_year, "expenditure_third_year":expenditure_third_year,
                        "details_source_income":details_source_income, "item_details_expense":item_details_expense,
                        "employee_details":employee_details, "sch_session_id":school_form_session, 
                        "bank_statement_first_year":saved_data.bank_statement_first_year if 
                        ((bank_statement_first_year == None) and retrieved_data ) else bank_statement_first_year,
                        "bank_statement_second_year":saved_data.bank_statement_second_year if 
                        ((bank_statement_second_year == None) and retrieved_data ) else bank_statement_second_year,
                        "bank_statement_third_year":saved_data.bank_statement_third_year if 
                        ((bank_statement_third_year == None) and retrieved_data ) else bank_statement_third_year,
                        "current_total_expenditure":current_total_expenditure if current_total_expenditure != '' else 0,"student_count_current_year":student_count_current_year,
                        "name_of_principal":name_of_principal,
                        "school_form_status":False,"student_category_id" : int(student_category) if student_category else None,
                        "text_field_1":"Draft","text_field_2":"Draft","text_field_3":"Draft"}) 

            data = SchoolForm.objects.create(name = data_draft.name, address = data_draft.address, email=data_draft.email,
                pincode = data_draft.pincode, mobile = data_draft.mobile, landline_no=data_draft.landline_no, authority_name=data_draft.authority_name,
                district = data_draft.district, taluka = data_draft.taluka, mulgaon = data_draft.mulgaon, organization_started=data_draft.organization_started,
                is_org_register= data_draft.is_org_register, org_register_certificate=data_draft.org_register_certificate, 
                bank_name = data_draft.bank_name,account_no = data_draft.account_no,account_holder = data_draft.account_holder,
                branch_name = data_draft.branch_name,ifsc_code=data_draft.ifsc_code, is_scholarship_recevied=data_draft.is_scholarship_recevied,
                cancelled_cheque=data_draft.cancelled_cheque,student_book_count_first_year=data_draft.student_book_count_first_year,
                student_book_count_second_year=data_draft.student_book_count_second_year, 
                student_book_count_third_year=data_draft.student_book_count_third_year, expenditure_first_year=data_draft.expenditure_first_year,
                expenditure_second_year=data_draft.expenditure_second_year, expenditure_third_year=data_draft.expenditure_third_year,
                details_source_income=data_draft.details_source_income, item_details_expense=data_draft.item_details_expense,
                employee_details=data_draft.employee_details, sch_session_id = school_form_session,
                bank_statement_first_year=data_draft.bank_statement_first_year,
                bank_statement_second_year=data_draft.bank_statement_second_year,
                bank_statement_third_year=data_draft.bank_statement_third_year,
                current_total_expenditure=data_draft.current_total_expenditure,
                student_count_current_year=data_draft.student_count_current_year,
                name_of_principal=data_draft.name_of_principal,
                other_taluka=data_draft.other_taluka, other_district=data_draft.other_district,
                student_category = data_draft.student_category,text_field_1 = "Draft",
                text_field_2 = "Draft",text_field_3 = "Draft")

            # data = SchoolForm.objects.create(name = name, address = address, email=email,
            #     pincode = pincode, mobile = mobile, landline_no=landline_no, authority_name=authority_name,
            #     district = district, taluka = taluka, mulgaon = mulgaon, organization_started=organization_started,
            #     is_org_register= is_org_register, org_register_certificate=saved_data.org_register_certificate if 
            #     ((org_register_certificate == None) and retrieved_data ) else org_register_certificate, 
            #     bank_name = bank_name,account_no = account_no,account_holder = account_holder,
            #     branch_name = branch_name,ifsc_code=ifsc_code, is_scholarship_recevied=is_scholarship_recevied,
            #     cancelled_cheque=saved_data.cancelled_cheque if 
            #     ((cancelled_cheque == None) and retrieved_data ) else cancelled_cheque,student_book_count_first_year=student_book_count_first_year,
            #     student_book_count_second_year=student_book_count_second_year, 
            #     student_book_count_third_year=student_book_count_third_year, expenditure_first_year=expenditure_first_year,
            #     expenditure_second_year=expenditure_second_year, expenditure_third_year=expenditure_third_year,
            #     details_source_income=details_source_income, item_details_expense=item_details_expense,
            #     employee_details=employee_details, sch_session_id = int(school_form_session), bank_statement=saved_data.bank_statement if 
            #     ((bank_statement == None) and retrieved_data ) else bank_statement,
            #     name_of_principal=name_of_principal)


            created_updated(SchoolForm, request)

            if data_draft:
                return render(request, "school_form_submitted_successfully.html")
            else:
                return HttpResponse("Data not submitted!")

        #save 
        elif action == "save":
            data,is_created = SchoolFormDraft.objects.update_or_create(email = request.user.email,sch_session_id=school_form_session,
                defaults = {
                        "other_taluka":other_taluka, 
                        "other_district":other_district,
                        "name":name, "address":address, 
                        "pincode":pincode, "mobile":mobile, "landline_no":landline_no, "authority_name":authority_name,
                        "district":district, "taluka": taluka, "mulgaon":mulgaon, 
                        "organization_started":organization_started if organization_started != '' else None,
                        "is_org_register":is_org_register, "org_register_certificate":saved_data.org_register_certificate if 
                        ((org_register_certificate == None) and retrieved_data ) else org_register_certificate, 
                        "bank_name":bank_name,"account_no":account_no,"account_holder":account_holder,
                        "branch_name":branch_name,"ifsc_code":ifsc_code, "is_scholarship_recevied":is_scholarship_recevied,
                        "cancelled_cheque":saved_data.cancelled_cheque if 
                        ((cancelled_cheque == None) and retrieved_data ) else cancelled_cheque,
                        "student_book_count_first_year":student_book_count_first_year,
                        "student_book_count_second_year":student_book_count_second_year, 
                        "student_book_count_third_year":student_book_count_third_year, "expenditure_first_year":expenditure_first_year,
                        "expenditure_second_year":expenditure_second_year, "expenditure_third_year":expenditure_third_year,
                        "details_source_income":details_source_income, "item_details_expense":item_details_expense,
                        "employee_details":employee_details, "sch_session_id":school_form_session, 
                        "bank_statement_first_year":saved_data.bank_statement_first_year if 
                        ((bank_statement_first_year == None) and retrieved_data ) else bank_statement_first_year,
                        "bank_statement_second_year":saved_data.bank_statement_second_year if 
                        ((bank_statement_second_year == None) and retrieved_data ) else bank_statement_second_year,
                        "bank_statement_third_year":saved_data.bank_statement_third_year if 
                        ((bank_statement_third_year == None) and retrieved_data ) else bank_statement_third_year,
                        "current_total_expenditure":current_total_expenditure if current_total_expenditure != '' else 0,"student_count_current_year":student_count_current_year,
                        "name_of_principal":name_of_principal,
                        "school_form_status":True,"student_category_id" : int(student_category) if student_category else None,
                        "text_field_1":"Draft","text_field_2":"Draft","text_field_3":"Draft"
                        }) 
            
            created_updated(SchoolFormDraft, request)

            if data:
                return render(request,"school_form_save_successfully.html")
            else:
                return HttpResponse("Data not SAVED!")
                    
            
        else:
            return HttpResponse("No action found!")


#AnganwadiFormView
@method_decorator(login_required, name='dispatch')
class AnganwadiFormView(View):
    def get(self,request,*args, **kwargs):

        action = request.GET.get('action',None)

        # Fetch data from typemaster 
        talukas = TypeMaster.objects.filter(category = "type_taluka").all()
        districts = TypeMaster.objects.filter(category = "type_district").all()
        hostel_details = TypeMaster.objects.filter(category = "hostel_details_type").all()


        # Loading district in Vachanalay form
        if action == 'district':
            parent_id   = request.GET.get('parent_id',None)
            if parent_id:
                district_data = list(TypeMaster.objects.filter(parent_id=int(parent_id),display_flag=1).values("name"))
                return JsonResponse(district_data, safe=False)

        # Get current year id from session.
        current_year_id = schSession.objects.get(is_default = True)

        # Get submitted and saved form status for current year.
        vachanalay_submitted_form = AnganwadiForm.objects.filter(email = request.user.email,sch_session_id= current_year_id.id).exists()
        saved_form = AnganwadiFormDraft.objects.filter(email = request.user.email,sch_session_id= current_year_id.id).exists()


        session_data = schSession.objects.all()
        user_data = UserDetails.objects.get(user_id=request.user.id)
       
        if vachanalay_submitted_form:

            return render(request, "anganwadi_one_time_save_successfully.html")
           
        elif saved_form:
            form_saved_data = AnganwadiFormDraft.objects.get(email = request.user.email,sch_session_id= current_year_id.id)
            selected_district_name = TypeMaster.objects.get(id=form_saved_data.district) if TypeMaster.objects.filter(id=form_saved_data.district).exists() else ""
            district_id = form_saved_data.district
            if district_id != "" and district_id != None:
                talukas = TypeMaster.objects.filter(category = "type_taluka",parent_id = district_id).all()

            date_organization_started = form_saved_data.organization_started.strftime('%Y-%m-%d') if form_saved_data.organization_started else ''

            context = {
                    
                    "talukas":talukas,
                    "districts":districts,
                    "form_saved_data":form_saved_data,
                    "selected_district_name":selected_district_name,
                    "date_organization_started":date_organization_started ,
                    "hostel_details":hostel_details,
                    "session_data":session_data,
                    "user_data":user_data,
                    "District_id":int(form_saved_data.district) if (form_saved_data.district) != None else 0,
                    "current_year_id":current_year_id


                }
               
            return render(request,"create_anganwadi_form.html",context)

        else:
        
            context = {
                    'session_data':session_data,
                    "talukas":talukas,
                    "districts":districts,
                    "user_data":user_data,
                    "hostel_details":hostel_details,
                    "current_year_id":current_year_id
                }

            return render(request,"create_anganwadi_form.html",context)


     # Create
    def post(self,request,*args, **kwargs):
        
        action = request.POST.get('action',None)


        name = request.POST.get('name', None)
        email = request.user.email
        address = request.POST.get('address', None)
        pincode = request.POST.get('pincode', None)
        authority_name = request.POST.get('authority_name', None)
        mobile = request.POST.get('mobile', None)
        landline_no = request.POST.get('landline_no', None)
        district = request.POST.get('district', None)
        taluka = request.POST.get('taluka', None)
        mulgaon = request.POST.get('mulgaon', ' ')
        organization_started = request.POST.get('organization_started', None)
        is_org_register = request.POST.get('is_org_register', None)
        org_register_certificate = request.FILES.get('org_register_certificate', None)
        print("org_register_certificate",org_register_certificate)
        bank_name = request.POST.get('bank_name', None)
        account_no = request.POST.get('account_no', None)
        account_holder = request.POST.get('account_holder', None)
        branch_name = request.POST.get('branch_name', None)
        ifsc_code = request.POST.get('ifsc_code', None)
        is_scholarship_recevied = request.POST.get('is_scholarship_recevied', None)
        cancelled_cheque = request.FILES.get('cancelled_cheque', None)
        student_book_count_first_year = request.POST.get('student_book_count_first_year', None)
        student_book_count_second_year = request.POST.get('student_book_count_second_year', None)
        student_book_count_third_year = request.POST.get('student_book_count_third_year', None)
        expenditure_first_year = request.POST.get('expenditure_first_year', None)
        expenditure_second_year = request.POST.get('expenditure_second_year', None)
        expenditure_third_year = request.POST.get('expenditure_third_year', None)
        details_source_income = request.POST.get('details_source_income', None)
        bank_statement_first_year = request.FILES.get('bank_statement_first_year', None)
        bank_statement_second_year = request.FILES.get('bank_statement_second_year', None)
        bank_statement_third_year = request.FILES.get('bank_statement_third_year', None)
        current_total_expenditure = request.POST.get('current_total_expenditure',None)
        student_count_current_year = request.POST.get('student_count_current_year',None)
        item_details_expense = request.POST.get('item_details_expense', None)
        employee_details = request.POST.get('employee_details', None)
        anganwadi_form_session = request.POST.get('anganwadi_form_session', None)
        group_photo = request.FILES.get('group_photo', None)
        other_taluka = request.POST.get('other_taluka', None)
        other_district = request.POST.get('other_district', None)
        anganwadi_form_session = int(anganwadi_form_session)

        application_type = "Anganwadi Form"
        # Student Category ID
        # anganwadi_form_category = StudentCategory.objects.get(status_code=1,application_type = application_type,student_category_session = anganwadi_form_session)
        # student_category = anganwadi_form_category.id

        if StudentCategory.objects.filter(status_code=1,application_type = application_type,student_category_session = anganwadi_form_session).exists():
            anganwadi_form_category = StudentCategory.objects.get(status_code=1,application_type = application_type,student_category_session = anganwadi_form_session)
            student_category = anganwadi_form_category.id
        else:
            student_category = False
            
        id = request.POST.get('id',None)

        if id:
            retrieved_data = True
            saved_data = AnganwadiFormDraft.objects.get(id = id)            
        else:
            retrieved_data = False

        #submit
        if action == "submit":      

            data_draft,is_created = AnganwadiFormDraft.objects.update_or_create(email = request.user.email,sch_session_id=anganwadi_form_session,
                defaults = {
                        "other_taluka":other_taluka, 
                        "other_district":other_district,
                        "name":name, "address":address, 
                        "pincode":pincode, "mobile":mobile, "landline_no":landline_no, "authority_name":authority_name,
                        "district":district, "taluka": taluka, "mulgaon":mulgaon, 
                        "organization_started":organization_started if organization_started != '' else None,
                        "is_org_register":is_org_register, "org_register_certificate":saved_data.org_register_certificate if 
                        ((org_register_certificate == None) and retrieved_data ) else org_register_certificate, 
                        "bank_name":bank_name,"account_no":account_no,"account_holder":account_holder,
                        "branch_name":branch_name,"ifsc_code":ifsc_code, "is_scholarship_recevied":is_scholarship_recevied,
                        "cancelled_cheque":saved_data.cancelled_cheque if 
                        ((cancelled_cheque == None) and retrieved_data ) else cancelled_cheque,
                        "student_book_count_first_year":student_book_count_first_year,
                        "student_book_count_second_year":student_book_count_second_year, 
                        "student_book_count_third_year":student_book_count_third_year, "expenditure_first_year":expenditure_first_year,
                        "expenditure_second_year":expenditure_second_year, "expenditure_third_year":expenditure_third_year,
                        "details_source_income":details_source_income, "item_details_expense":item_details_expense,
                        "employee_details":employee_details, "sch_session_id":anganwadi_form_session, 
                        "bank_statement_first_year":saved_data.bank_statement_first_year if 
                        ((bank_statement_first_year == None) and retrieved_data ) else bank_statement_first_year,
                        "bank_statement_second_year":saved_data.bank_statement_second_year if 
                        ((bank_statement_second_year == None) and retrieved_data ) else bank_statement_second_year,
                        "bank_statement_third_year":saved_data.bank_statement_third_year if 
                        ((bank_statement_third_year == None) and retrieved_data ) else bank_statement_third_year,
                        "current_total_expenditure":current_total_expenditure if current_total_expenditure != '' else 0,"student_count_current_year":student_count_current_year,
                        "group_photo":saved_data.group_photo if 
                        ((group_photo == None) and retrieved_data ) else group_photo,
                        "anganwadi_form_status":False,"student_category_id" : int(student_category) if student_category else None,
                        "text_field_1":"Draft","text_field_2":"Draft","text_field_3":"Draft"
                        }) 

            data = AnganwadiForm.objects.create(name = data_draft.name, address = data_draft.address, email=data_draft.email,
                pincode = data_draft.pincode, mobile = data_draft.mobile, landline_no=data_draft.landline_no, authority_name=data_draft.authority_name,
                district = data_draft.district, taluka = data_draft.taluka, mulgaon = data_draft.mulgaon, organization_started=data_draft.organization_started,
                is_org_register= data_draft.is_org_register, org_register_certificate=data_draft.org_register_certificate, 
                bank_name = data_draft.bank_name,account_no = data_draft.account_no,account_holder = data_draft.account_holder,
                branch_name = data_draft.branch_name,ifsc_code=data_draft.ifsc_code, is_scholarship_recevied=data_draft.is_scholarship_recevied,
                 cancelled_cheque=data_draft.cancelled_cheque,student_book_count_first_year=data_draft.student_book_count_first_year,
                student_book_count_second_year=data_draft.student_book_count_second_year, 
                student_book_count_third_year=data_draft.student_book_count_third_year, expenditure_first_year=data_draft.expenditure_first_year,
                expenditure_second_year=data_draft.expenditure_second_year, expenditure_third_year=data_draft.expenditure_third_year,
                details_source_income=data_draft.details_source_income, item_details_expense=data_draft.item_details_expense,
                employee_details=data_draft.employee_details, sch_session_id = anganwadi_form_session, 
                bank_statement_first_year=data_draft.bank_statement_first_year,
                bank_statement_second_year=data_draft.bank_statement_second_year,
                bank_statement_third_year=data_draft.bank_statement_third_year,
                current_total_expenditure=data_draft.current_total_expenditure,
                student_count_current_year=data_draft.student_count_current_year,
                group_photo = data_draft.group_photo,
                other_taluka=data_draft.other_taluka, other_district=data_draft.other_district,
                student_category = data_draft.student_category,text_field_1 = "Draft",
                text_field_2 = "Draft",text_field_3 = "Draft")

             # data = AnganwadiForm.objects.create(name = name, address = address, email=email,
             #    pincode = pincode, mobile = mobile, landline_no=landline_no, authority_name=authority_name,
             #    district = district, taluka = taluka, mulgaon = mulgaon, organization_started=organization_started,
             #    is_org_register= is_org_register, org_register_certificate=saved_data.org_register_certificate if 
             #    ((org_register_certificate == None) and retrieved_data ) else org_register_certificate, 
             #    bank_name = bank_name,account_no = account_no,account_holder = account_holder,
             #    branch_name = branch_name,ifsc_code=ifsc_code, is_scholarship_recevied=is_scholarship_recevied,
             #     cancelled_cheque=saved_data.cancelled_cheque if 
             #    ((cancelled_cheque == None) and retrieved_data ) else cancelled_cheque,student_book_count_first_year=student_book_count_first_year,
             #    student_book_count_second_year=student_book_count_second_year, 
             #    student_book_count_third_year=student_book_count_third_year, expenditure_first_year=expenditure_first_year,
             #    expenditure_second_year=expenditure_second_year, expenditure_third_year=expenditure_third_year,
             #    details_source_income=details_source_income, item_details_expense=item_details_expense,
             #    employee_details=employee_details, sch_session_id = int(anganwadi_form_session), 
             #    bank_statement=saved_data.bank_statement if ((bank_statement == None) and retrieved_data ) else bank_statement,
             #    group_photo = saved_data.group_photo if 
             #    ((group_photo == None) and retrieved_data ) else group_photo)

            created_updated(AnganwadiForm, request)

            if data:
                return render(request, "anaganwadi_form_submitted_successfully.html")
            else:
                return HttpResponse("Data not submitted!")

        #save
        elif action == "save":
            
            data,is_created = AnganwadiFormDraft.objects.update_or_create(email = request.user.email,sch_session_id=anganwadi_form_session,
                defaults = {
                        "other_taluka":other_taluka, 
                        "other_district":other_district,
                        "name":name, "address":address, 
                        "pincode":pincode, "mobile":mobile, "landline_no":landline_no, "authority_name":authority_name,
                        "district":district, "taluka": taluka, "mulgaon":mulgaon, 
                        "organization_started":organization_started if organization_started != '' else None,
                        "is_org_register":is_org_register, "org_register_certificate":saved_data.org_register_certificate if 
                        ((org_register_certificate == None) and retrieved_data ) else org_register_certificate, 
                        "bank_name":bank_name,"account_no":account_no,"account_holder":account_holder,
                        "branch_name":branch_name,"ifsc_code":ifsc_code, "is_scholarship_recevied":is_scholarship_recevied,
                        "cancelled_cheque":saved_data.cancelled_cheque if 
                        ((cancelled_cheque == None) and retrieved_data ) else cancelled_cheque,
                        "student_book_count_first_year":student_book_count_first_year,
                        "student_book_count_second_year":student_book_count_second_year, 
                        "student_book_count_third_year":student_book_count_third_year, "expenditure_first_year":expenditure_first_year,
                        "expenditure_second_year":expenditure_second_year, "expenditure_third_year":expenditure_third_year,
                        "details_source_income":details_source_income, "item_details_expense":item_details_expense,
                        "employee_details":employee_details, "sch_session_id":anganwadi_form_session, 
                        "bank_statement_first_year":saved_data.bank_statement_first_year if 
                        ((bank_statement_first_year == None) and retrieved_data ) else bank_statement_first_year,
                        "bank_statement_second_year":saved_data.bank_statement_second_year if 
                        ((bank_statement_second_year == None) and retrieved_data ) else bank_statement_second_year,
                        "bank_statement_third_year":saved_data.bank_statement_third_year if 
                        ((bank_statement_third_year == None) and retrieved_data ) else bank_statement_third_year,
                        "current_total_expenditure":current_total_expenditure if current_total_expenditure != '' else 0,"student_count_current_year":student_count_current_year,
                        "group_photo":saved_data.group_photo if 
                        ((group_photo == None) and retrieved_data ) else group_photo,
                        "anganwadi_form_status":True,"student_category_id" : int(student_category) if student_category else None,
                        "text_field_1":"Draft","text_field_2":"Draft","text_field_3":"Draft"
                        }) 
          
            created_updated(AnganwadiFormDraft, request)
            if data:
                return render(request,"anganwadi_form_save_successfully.html")
            else:
                return HttpResponse("Data not SAVED!")
                    
            
        else:
            return HttpResponse("No action found!")


#InstitutionFormView
@method_decorator(login_required, name='dispatch')
class InstitutionFormView(View):
    def get(self,request,*args, **kwargs):

        action = request.GET.get('action',None)

        # Fetch data from typemaster 
        talukas = TypeMaster.objects.filter(category = "type_taluka").all()
        districts = TypeMaster.objects.filter(category = "type_district").all()
        hostel_details = TypeMaster.objects.filter(category = "hostel_details_type").all()


        # Loading district in Institution form
        if action == 'district':
            parent_id   = request.GET.get('parent_id',None)
            if parent_id:
                district_data = list(TypeMaster.objects.filter(parent_id=int(parent_id),display_flag=1).values("name"))
                return JsonResponse(district_data, safe=False)

        # Get current year id from session.
        current_year_id = schSession.objects.get(is_default = True)

        # Get submitted and saved form status for current year.
        institution_submitted_form = InstitutionForm.objects.filter(email = request.user.email,sch_session_id= current_year_id.id).exists()
        saved_form = InstitutionFormDraft.objects.filter(email = request.user.email,sch_session_id= current_year_id.id).exists()


        session_data = schSession.objects.all()
        user_data = UserDetails.objects.get(user_id=request.user.id)
       
        if institution_submitted_form:

            return render(request, "institution_one_time_save_successfully.html")
           
        elif saved_form:
            form_saved_data = InstitutionFormDraft.objects.get(email = request.user.email,sch_session_id= current_year_id.id)
            selected_district_name = TypeMaster.objects.get(id=form_saved_data.district) if TypeMaster.objects.filter(id=form_saved_data.district).exists() else ""
            district_id = form_saved_data.district
            if district_id != "" and district_id != None:
                talukas = TypeMaster.objects.filter(category = "type_taluka",parent_id = district_id).all()

            date_organization_started = form_saved_data.organization_started.strftime('%Y-%m-%d') if form_saved_data.organization_started else ''

            context = {
                    
                    "talukas":talukas,
                    "districts":districts,
                    "form_saved_data":form_saved_data,
                    "selected_district_name":selected_district_name,
                    "date_organization_started":date_organization_started ,
                    "hostel_details":hostel_details,
                    "session_data":session_data,
                    "user_data":user_data,
                    "District_id":int(form_saved_data.district) if (form_saved_data.district) != None else 0,
                    "current_year_id":current_year_id


                }
               
            return render(request,"create_institution_form.html",context)

        else:
        
            context = {
                    'session_data':session_data,
                    "talukas":talukas,
                    "districts":districts,
                    "user_data":user_data,
                    "hostel_details":hostel_details,
                    "current_year_id":current_year_id
                }

            return render(request,"create_institution_form.html",context)


     # Create
    def post(self,request,*args, **kwargs):
        
        action = request.POST.get('action',None)


        name = request.POST.get('name', None)
        email = request.user.email
        address = request.POST.get('address', None)
        pincode = request.POST.get('pincode', None)
        authority_name = request.POST.get('authority_name', None)
        mobile = request.POST.get('mobile', None)
        landline_no = request.POST.get('landline_no', None)
        district = request.POST.get('district', None)
        taluka = request.POST.get('taluka', None)
        mulgaon = request.POST.get('mulgaon', ' ')
        organization_started = request.POST.get('organization_started', None)
        is_org_register = request.POST.get('is_org_register', None)
        org_register_certificate = request.FILES.get('org_register_certificate', None)
        bank_name = request.POST.get('bank_name', None)
        account_no = request.POST.get('account_no', None)
        account_holder = request.POST.get('account_holder', None)
        branch_name = request.POST.get('branch_name', None)
        ifsc_code = request.POST.get('ifsc_code', None)
        is_scholarship_recevied = request.POST.get('is_scholarship_recevied', None)
        cancelled_cheque = request.FILES.get('cancelled_cheque', None)
        student_book_count_first_year = request.POST.get('student_book_count_first_year', None)
        student_book_count_second_year = request.POST.get('student_book_count_second_year', None)
        student_book_count_third_year = request.POST.get('student_book_count_third_year', None)
        expenditure_first_year = request.POST.get('expenditure_first_year', None)
        expenditure_second_year = request.POST.get('expenditure_second_year', None)
        expenditure_third_year = request.POST.get('expenditure_third_year', None)
        details_source_income = request.POST.get('details_source_income', None)
        bank_statement_first_year = request.FILES.get('bank_statement_first_year', None)
        bank_statement_second_year = request.FILES.get('bank_statement_second_year', None)
        bank_statement_third_year = request.FILES.get('bank_statement_third_year', None)
        current_total_expenditure = request.POST.get('current_total_expenditure',None)
        student_count_current_year = request.POST.get('student_count_current_year',None)
        item_details_expense = request.POST.get('item_details_expense', None)
        employee_details = request.POST.get('employee_details', None)
        institution_form_session = request.POST.get('institution_form_session', None)
        group_photo = request.FILES.get('group_photo', None)
        other_taluka = request.POST.get('other_taluka', None)
        other_district = request.POST.get('other_district', None)
        hostel_type = request.POST.get('hostel_type', None)
        institution_form_session = int(institution_form_session)

        application_type = "Institution Form"
        # Student Category ID
        # institution_form_category = StudentCategory.objects.get(status_code=1,application_type = application_type,student_category_session = institution_form_session)
        # student_category = institution_form_category.id
        if StudentCategory.objects.filter(status_code=1,application_type = application_type,student_category_session = institution_form_session).exists():
            institution_form_category = StudentCategory.objects.get(status_code=1,application_type = application_type,student_category_session = institution_form_session)
            student_category = institution_form_category.id
        else:
            student_category = False

        id = request.POST.get('id',None)

        if id:
            retrieved_data = True
            saved_data = InstitutionFormDraft.objects.get(id = id)            
        else:
            retrieved_data = False

        #submit
        if action == "submit": 

            data_draft,is_created = InstitutionFormDraft.objects.update_or_create(email = request.user.email,sch_session_id=institution_form_session,
                defaults = {
                        "other_taluka":other_taluka, 
                        "other_district":other_district,
                        "name":name, "address":address, 
                        "pincode":pincode, "mobile":mobile, "landline_no":landline_no, "authority_name":authority_name,
                        "district":district, "taluka": taluka, "mulgaon":mulgaon, 
                        "organization_started":organization_started if organization_started != '' else None,
                        "is_org_register":is_org_register, "org_register_certificate":saved_data.org_register_certificate if 
                        ((org_register_certificate == None) and retrieved_data ) else org_register_certificate, 
                        "bank_name":bank_name,"account_no":account_no,"account_holder":account_holder,
                        "branch_name":branch_name,"ifsc_code":ifsc_code, "is_scholarship_recevied":is_scholarship_recevied,
                        "cancelled_cheque":saved_data.cancelled_cheque if 
                        ((cancelled_cheque == None) and retrieved_data ) else cancelled_cheque,
                        "student_book_count_first_year":student_book_count_first_year,
                        "student_book_count_second_year":student_book_count_second_year, 
                        "student_book_count_third_year":student_book_count_third_year, "expenditure_first_year":expenditure_first_year,
                        "expenditure_second_year":expenditure_second_year, "expenditure_third_year":expenditure_third_year,
                        "details_source_income":details_source_income, "item_details_expense":item_details_expense,
                        "employee_details":employee_details, "sch_session_id":institution_form_session, 
                        "bank_statement_first_year":saved_data.bank_statement_first_year if 
                        ((bank_statement_first_year == None) and retrieved_data ) else bank_statement_first_year,
                        "bank_statement_second_year":saved_data.bank_statement_second_year if 
                        ((bank_statement_second_year == None) and retrieved_data ) else bank_statement_second_year,
                        "bank_statement_third_year":saved_data.bank_statement_third_year if 
                        ((bank_statement_third_year == None) and retrieved_data ) else bank_statement_third_year,
                        "current_total_expenditure":current_total_expenditure if current_total_expenditure != '' else 0,"student_count_current_year":student_count_current_year,
                        "group_photo":saved_data.group_photo if 
                        ((group_photo == None) and retrieved_data ) else group_photo,
                        "institution_form_status":False, "hostel_type":hostel_type,
                        "student_category_id" : int(student_category) if student_category else None,
                        "text_field_1":"Draft","text_field_2":"Draft","text_field_3":"Draft"
                        }) 

            data = InstitutionForm.objects.create(name = data_draft.name, address = data_draft.address, email=data_draft.email,
                pincode = data_draft.pincode, mobile = data_draft.mobile, landline_no=data_draft.landline_no, authority_name=data_draft.authority_name,
                district = data_draft.district, taluka = data_draft.taluka, mulgaon = data_draft.mulgaon, organization_started=data_draft.organization_started,
                is_org_register= data_draft.is_org_register, org_register_certificate=data_draft.org_register_certificate, 
                bank_name = data_draft.bank_name,account_no = data_draft.account_no,account_holder = data_draft.account_holder,
                branch_name = data_draft.branch_name,ifsc_code=data_draft.ifsc_code, is_scholarship_recevied=data_draft.is_scholarship_recevied,
                cancelled_cheque=data_draft.cancelled_cheque,student_book_count_first_year=data_draft.student_book_count_first_year,
                student_book_count_second_year=data_draft.student_book_count_second_year, 
                student_book_count_third_year=data_draft.student_book_count_third_year, expenditure_first_year=data_draft.expenditure_first_year,
                expenditure_second_year=data_draft.expenditure_second_year, expenditure_third_year=data_draft.expenditure_third_year,
                details_source_income=data_draft.details_source_income, item_details_expense=data_draft.item_details_expense,
                employee_details=data_draft.employee_details, sch_session_id = institution_form_session, 
                bank_statement_first_year=data_draft.bank_statement_first_year,
                bank_statement_second_year=data_draft.bank_statement_second_year,
                bank_statement_third_year=data_draft.bank_statement_third_year,
                current_total_expenditure=data_draft.current_total_expenditure,
                student_count_current_year=data_draft.student_count_current_year,
                group_photo = data_draft.group_photo, hostel_type=hostel_type,
                other_taluka=data_draft.other_taluka, other_district=data_draft.other_district,
                student_category = data_draft.student_category,text_field_1 = "Draft",
                text_field_2 = "Draft",text_field_3 = "Draft")

             # data = AnganwadiForm.objects.create(name = name, address = address, email=email,
             #    pincode = pincode, mobile = mobile, landline_no=landline_no, authority_name=authority_name,
             #    district = district, taluka = taluka, mulgaon = mulgaon, organization_started=organization_started,
             #    is_org_register= is_org_register, org_register_certificate=saved_data.org_register_certificate if 
             #    ((org_register_certificate == None) and retrieved_data ) else org_register_certificate, 
             #    bank_name = bank_name,account_no = account_no,account_holder = account_holder,
             #    branch_name = branch_name,ifsc_code=ifsc_code, is_scholarship_recevied=is_scholarship_recevied,
             #     cancelled_cheque=saved_data.cancelled_cheque if 
             #    ((cancelled_cheque == None) and retrieved_data ) else cancelled_cheque,student_book_count_first_year=student_book_count_first_year,
             #    student_book_count_second_year=student_book_count_second_year, 
             #    student_book_count_third_year=student_book_count_third_year, expenditure_first_year=expenditure_first_year,
             #    expenditure_second_year=expenditure_second_year, expenditure_third_year=expenditure_third_year,
             #    details_source_income=details_source_income, item_details_expense=item_details_expense,
             #    employee_details=employee_details, sch_session_id = int(anganwadi_form_session), 
             #    bank_statement=saved_data.bank_statement if ((bank_statement == None) and retrieved_data ) else bank_statement,
             #    group_photo = saved_data.group_photo if 
             #    ((group_photo == None) and retrieved_data ) else group_photo)

            created_updated(InstitutionForm, request)

            if data:
                return render(request, "institution_form_submitted_successfully.html")
            else:
                return HttpResponse("Data not submitted!")

        #save
        elif action == "save":
            
            data,is_created = InstitutionFormDraft.objects.update_or_create(email = request.user.email,sch_session_id=institution_form_session,
                defaults = {
                        "other_taluka":other_taluka, 
                        "other_district":other_district,
                        "name":name, "address":address, 
                        "pincode":pincode, "mobile":mobile, "landline_no":landline_no, "authority_name":authority_name,
                        "district":district, "taluka": taluka, "mulgaon":mulgaon, 
                        "organization_started":organization_started if organization_started != '' else None,
                        "is_org_register":is_org_register, "org_register_certificate":saved_data.org_register_certificate if 
                        ((org_register_certificate == None) and retrieved_data ) else org_register_certificate, 
                        "bank_name":bank_name,"account_no":account_no,"account_holder":account_holder,
                        "branch_name":branch_name,"ifsc_code":ifsc_code, "is_scholarship_recevied":is_scholarship_recevied,
                        "cancelled_cheque":saved_data.cancelled_cheque if 
                        ((cancelled_cheque == None) and retrieved_data ) else cancelled_cheque,
                        "student_book_count_first_year":student_book_count_first_year,
                        "student_book_count_second_year":student_book_count_second_year, 
                        "student_book_count_third_year":student_book_count_third_year, "expenditure_first_year":expenditure_first_year,
                        "expenditure_second_year":expenditure_second_year, "expenditure_third_year":expenditure_third_year,
                        "details_source_income":details_source_income, "item_details_expense":item_details_expense,
                        "employee_details":employee_details, "sch_session_id":institution_form_session, 
                       "bank_statement_first_year":saved_data.bank_statement_first_year if 
                        ((bank_statement_first_year == None) and retrieved_data ) else bank_statement_first_year,
                        "bank_statement_second_year":saved_data.bank_statement_second_year if 
                        ((bank_statement_second_year == None) and retrieved_data ) else bank_statement_second_year,
                        "bank_statement_third_year":saved_data.bank_statement_third_year if 
                        ((bank_statement_third_year == None) and retrieved_data ) else bank_statement_third_year,
                        "current_total_expenditure":current_total_expenditure if current_total_expenditure != '' else 0,"student_count_current_year":student_count_current_year,
                        "group_photo":saved_data.group_photo if 
                        ((group_photo == None) and retrieved_data ) else group_photo,
                        "institution_form_status":False, "hostel_type":hostel_type,
                        "student_category_id" : int(student_category) if student_category else None,
                        "text_field_1":"Draft","text_field_2":"Draft","text_field_3":"Draft"
                        }) 
          
                        
            created_updated(InstitutionFormDraft, request)

            if data:
                return render(request,"institution_form_save_successfully.html")
            else:
                return HttpResponse("Data not SAVED!")
                    
            
        else:
            return HttpResponse("No action found!")


#DistrictID
class DistrictID(View):
    def get(self, request, *args, **kwargs):

        district_ID = request.GET.get('id')
        details = StSchFormDetails.objects.filter(id=district_ID).values()
        print("Details----", details)

        return JsonResponse(details[0])


#ApplicantProfileDetails
@method_decorator(login_required, name='dispatch')
class ApplicantProfileDetails(View):
    def get(self, request, *args, **kwargs):

        action = request.GET.get('action',None)
        email = request.user.email

        # Fetch data from typemaster 
        talukas = TypeMaster.objects.filter(category = "type_taluka").all()
        districts = TypeMaster.objects.filter(category = "type_district").all()
        current_education_type = TypeMaster.objects.filter(category = "current_education_type").all().order_by('sequence')
        passed_education_type = TypeMaster.objects.filter(category = "passed_education_type").all().order_by('sequence')

        session_data = schSession.objects.all()
        user_data = UserDetails.objects.get(user_id=request.user.id)
        current_year_id = schSession.objects.get(is_default = True)        
        roles = user_data.role.all()

        # Get current year id from session.
        current_year_id = schSession.objects.get(is_default = True)

        if action == 'scholarship':
            form_saved_data = StSchFormDetails.objects.get(email=request.user.email, sch_session_id= current_year_id.id)
            context={"form_saved_data":form_saved_data, 
                    'session_data':session_data,
                    "talukas":talukas,
                    "districts":districts,
                    "current_education_type":current_education_type,
                    "passed_education_type":passed_education_type,
                    "user_data":user_data,
                    "District_id":int(form_saved_data.district) if (form_saved_data.district) != None else 0
                    }
            return render(request,'readonly_student_scholarship_details_form.html',context)

        elif action == 'loan':
            form_saved_data = StLoanFormDetails.objects.get(email=request.user.email, sch_session_id=current_year_id.id)
            context={"form_saved_data":form_saved_data,
                    'session_data':session_data,
                    "talukas":talukas,
                    "districts":districts,
                    "current_education_type":current_education_type,
                    "passed_education_type":passed_education_type,
                    "user_data":user_data,
                    "District_id":int(form_saved_data.district) if (form_saved_data.district) != None else 0
                    }
            return render(request,'readonly_loan_scholarship_details_form.html',context)

        elif action == 'school':
            form_saved_data = SchoolForm.objects.get(email=request.user.email,sch_session_id= current_year_id.id)
            date_organization_started = form_saved_data.organization_started.strftime('%Y-%m-%d') if form_saved_data.organization_started else ''
            context={"form_saved_data":form_saved_data,
                    'session_data':session_data,
                    "talukas":talukas,
                    "districts":districts,
                    "current_education_type":current_education_type,
                    "passed_education_type":passed_education_type,
                    "user_data":user_data,
                    "District_id":int(form_saved_data.district) if (form_saved_data.district) != None else 0,
                    "date_organization_started":date_organization_started
                    }
            return render(request,'readonly_school_form.html',context)

        elif action == 'vachanalay':
            form_saved_data = VachnalayaForm.objects.get(email=request.user.email, sch_session_id= current_year_id.id)
            # date_organization_started = form_saved_data.organization_started.strftime('%Y-%m-%d') if form_saved_data.organization_started else ''
            date_organization_started = form_saved_data.organization_started.strftime('%Y-%m-%d') if form_saved_data.organization_started else ''

            context={"form_saved_data":form_saved_data,
                    "date_organization_started":date_organization_started,
                    'session_data':session_data,
                    "talukas":talukas,
                    "districts":districts,
                    "current_education_type":current_education_type,
                    "passed_education_type":passed_education_type,
                    "user_data":user_data,
                    "District_id":int(form_saved_data.district) if (form_saved_data.district) != None else 0
                    }
            return render(request,'readonly_vachanalay_form.html',context)

        elif action == 'anaganwadi':
            form_saved_data = AnganwadiForm.objects.get(email=request.user.email, sch_session_id= current_year_id.id)
            date_organization_started = form_saved_data.organization_started.strftime('%Y-%m-%d') if form_saved_data.organization_started else ''
            hostel_details = TypeMaster.objects.filter(category = "hostel_details_type").all()

            context={"form_saved_data":form_saved_data,
                    'session_data':session_data,
                    "talukas":talukas,
                    "districts":districts,
                    "current_education_type":current_education_type,
                    "passed_education_type":passed_education_type,
                    "user_data":user_data,
                    "date_organization_started":date_organization_started,
                    "District_id":int(form_saved_data.district) if (form_saved_data.district) != None else 0,
                    "hostel_details":hostel_details
                    }
            return render(request,'readonly_anganwadi_form.html',context)

        elif action == 'institution':
            form_saved_data = InstitutionForm.objects.get(email=request.user.email, sch_session_id= current_year_id.id)
            date_organization_started = form_saved_data.organization_started.strftime('%Y-%m-%d') if form_saved_data.organization_started else ''
            hostel_details = TypeMaster.objects.filter(category = "hostel_details_type").all()

            context={"form_saved_data":form_saved_data,
                    'session_data':session_data,
                    "talukas":talukas,
                    "districts":districts,
                    "current_education_type":current_education_type,
                    "passed_education_type":passed_education_type,
                    "user_data":user_data,
                    "date_organization_started":date_organization_started,
                    "District_id":int(form_saved_data.district) if (form_saved_data.district) != None else 0,
                    "hostel_details":hostel_details
                    }
            return render(request,'readonly_institution_form.html',context)
            
        else:
            # Current User Role
            for i in roles:
                role = i.name
            print("role:-",role)
            # Check Current user role exist or not  in Privileges
            privileges = Privileges.objects.filter(name = role).exists()
            # Get admin_privileges
            admin_privileges_obj = TypeMaster.objects.filter(status_code = 1,category = "admin_privileges").all()
            admin_privileges_list = [i.name for i in admin_privileges_obj]
        
            if role in admin_privileges_list:
                status = "Admin"
            else:  
                try:
                    # forms type
                    form_types = TypeMaster.objects.filter(status_code=1,category = "form_type").all()
                    for i in form_types:
                        # Db Model name
                        table_name = i.name
                        # Get Model Object
                        model = apps.get_model('sat_application',table_name)
                        # Check User Exist or not
                        if (model.objects.filter(status_code = 1,email = email,sch_session_id = current_year_id.id).exists()):
                            user_status_data = model.objects.filter(status_code = 1,email = email,sch_session_id = current_year_id.id).first()
                            status_1 = user_status_data.text_field_1    # phase 1 status
                            status_2 = user_status_data.text_field_2    # phase 2 status
                            status_3 = user_status_data.text_field_3    # phase 3 status
                            student_form_session = user_status_data.sch_session.year
                        else:
                            status = ""
                            print("1:Else Data Not Available")
                    
                    # Check Status 
                    if(status_1 != "Draft" and status_2 == "Draft" and status_3 == "Draft"):
                        status = TypeMaster.objects.get(status_code=1,category = "form_status",name = status_1)
                        status = str(status.description).replace("_", student_form_session)
    
                    elif(status_1 == "Shortlisted" and status_2 != "Draft" and status_3 == "Draft"):
                        status = TypeMaster.objects.get(status_code=1,category = "form_status_select",name = status_2)
                        status = str(status.description).replace("_", student_form_session)

                    elif(status_1 == "Shortlisted" and status_2 == "Selected" and status_3 != "Draft"):
                        status = TypeMaster.objects.get(status_code=1,category = "form_status_recieved",name = status_3)
                        status = str(status.description).replace("_", student_form_session)

                    else:
                        status = TypeMaster.objects.get(status_code=1,category = "form_status",name = "Draft")
                        status = str(status.description).replace("_", student_form_session)
                    
                except:
                    status = "Your application is Not Submitted"
                    
            context = {
            "user_data":user_data,
            'roles': roles,
            'status':status
            }
            print("context", context)
            return render(request, 'applicant_profile_details.html', context)

#StudentCategoryView
@method_decorator(login_required, name='dispatch')
class StudentCategoryView(View):

    def __init__(self,*args,**kwargs):
        path = os.getcwd()

        with open(os.path.join(path, "form_jsons/StudentCategory.json"), 'r') as file:
            self.queryset = file.read()

    def get(self,request,*args, **kwargs):
        file = self.queryset 
        queryset_dict = json.loads(file)

        action = request.GET.get('action',None)
        instance_id = request.GET.get('id',None)
        search = request.GET.get('search',None)
        entries = request.GET.get('entries', '5')

        table_values = queryset_dict['HTML_table']['values']
        list_table_values = [x["name"] for x in table_values]
        
        # Fetching application type
        application_type = TypeMaster.objects.filter(status_code=1,category = "application_type").all()
        # Fetching current education type courses
        courses = TypeMaster.objects.filter(status_code=1,category = "current_education_type").all()
        
        # Get current year id from session.
        current_year_id = schSession.objects.get(is_default = True)
        
        if action == 'create':  
            context = {
                "redirect":"studentcategory",
                "application_type":application_type,
                "courses":courses,
                "current_year_id":current_year_id
            }       
            return render(request, 'create_student_category.html', context)

        elif action == 'edit':
            if instance_id:
                # Id 
                data = StudentCategory.objects.filter(status_code=1).get(id=instance_id)
                # Courses String
                courses_link_list = str(data.courses_link[1:-1])
                # Courses List
                new_list = courses_link_list.split(", ")

                selected_courses_link_list = []
                for i in new_list:
                    new_item = i[1:-1]
                    selected_courses_link_list.append(new_item)

                # json_string = str(queryset_dict)
                context = {
                    "data":data, "redirect":"studentcategory",
                    "application_type":application_type,
                    "courses":courses,
                    "selected_courses_link_list":selected_courses_link_list 
                    }
                return render(request,'edit_student_category.html',context)

        elif action == 'delete':    
            if instance_id:
                return self.delete(request)

        elif action == 'search':
            data = StudentCategory.objects.filter(Q(category_name__icontains=search)|Q(application_type__icontains=search)|Q(amt_for_candidates__icontains=search)|Q(total_amt__icontains=search),student_category_session = current_year_id.id,status=1).all()

           
            #TODO: Uncomment if checkbox field is included in the form.
           
        

            context = {
                "data":data, 
                "values":table_values, 
                "JsonForm": queryset_dict, 
                "redirect":"studentcategory",
                "application_type":application_type,
                "courses":courses
                }
            return render(request,'table_student_category.html',context)

        # start category exist
        elif action == 'check_category_exist':
            application_type = request.GET.get('application_type',None)
            student_category_session = request.GET.get('student_category_session',None)
            selected_courses = request.GET.get('selected_courses',None)     # String value of category
            student_category_session = int(student_category_session)
            # List of Selected Courses
            selected_courses = str(selected_courses).split(",")
            # Get all data of application 
            check_category_exist_data = StudentCategory.objects.filter(application_type = application_type,student_category_session = student_category_session)
            # List of Category from DB
            list_of_category = []
            existed = False         # Default True
            
            # All Category Data
            for i in check_category_exist_data:
                courses = str(i.courses_link)
                courses_lst = courses[1:-1].split(",")
                list1_courses = []
                for i in courses_lst:
                    value = i.replace("'","")       # Replacing ' to "" (Space) in category names from DB
                    list1_courses.append(value)
                list_of_category.append(list1_courses)
            # if category existed existed = True
            for row in list_of_category:
                if row == selected_courses:
                    existed = True
            # If category existed 
            if existed:
                return JsonResponse({'status':'Exist','msg': 'Category Already Exist...'})
            else:
                return JsonResponse({'status':'Not Exist','msg': 'Category Not Exist'})

        # End 
        else:                           
            data = StudentCategory.objects.filter(status_code = 1,student_category_session = current_year_id.id).only(*list_table_values)


            #TODO: Uncomment if checkbox field is included in the form.
            
            
            context = {
                "data":data,
                "redirect":"studentcategory",
                "values":table_values,
                "JsonForm": queryset_dict,
                "application_type":application_type,
                "courses":courses,
                "current_year_id":current_year_id
            }
            return render(request,'table_student_category.html',context)

    # Create
    def post(self,request,*args, **kwargs):
        if '_put' in request.POST:
            return self.put(request)  
        
        category_name = request.POST.get('category_name', None)
        student_category_session = request.POST.get('student_category_session', None)
        application_type = request.POST.get('application_type', None)
        no_of_candidates = request.POST.get('no_of_candidates', None)
        amt_for_candidates = request.POST.get('amt_for_candidates', None)
        courses_link = request.POST.getlist('courses_link', None)
        total_amt = request.POST.get('total_amt', None)
        student_category_session = int(student_category_session)
        
        data = StudentCategory.objects.create(category_name = category_name, student_category_session_id= student_category_session, 
                application_type = application_type, no_of_candidates = no_of_candidates, 
                amt_for_candidates = amt_for_candidates, courses_link = courses_link, total_amt = total_amt)

        created_updated(StudentCategory, request)
        if data:
            messages.success(request, f'{category_name} - Student Category Created!')
            return redirect('studentcategory')
        else:
            messages.error(request, f'{category_name} - Student Category Not Created!')
            return redirect('studentcategory')

    # Edit
    def put(self,request,*args,**kwargs):
        
        category_name = request.POST.get('category_name', None)
        student_category_session = request.POST.get('student_category_session', None)
        application_type = request.POST.get('application_type', None)
        no_of_candidates = request.POST.get('no_of_candidates', None)
        amt_for_candidates = request.POST.get('amt_for_candidates', None)
        courses_link = request.POST.getlist('courses_link', None)
        total_amt = request.POST.get('total_amt', None)
        student_category_session = int(student_category_session)
        id = request.POST.get('id',None)

        #TODO: Implement IF validation if file field available in the form

        #if file:
            #obj = StudentCategory .objects.get(id=id)
            #''''''
            #obj.save()
        # TODO: Remove file field
        # Data Updating 
        update = StudentCategory.objects.filter(id=id).update(category_name = category_name, 
                student_category_session_id = student_category_session, 
                application_type = application_type, no_of_candidates = no_of_candidates, amt_for_candidates = amt_for_candidates, 
                courses_link = courses_link, total_amt = total_amt)
        
        created_updated(StudentCategory, request)
        if update:
            messages.success(request, 'Student Category Updated!')
            return redirect('studentcategory')
        else:
            messages.success(request, 'Student Category Not Updated!')
            return redirect('studentcategory')
    # Delete
    def delete(self,request,*args,**kwargs):
        id = request.GET.get('id',None)
        student_category_name = StudentCategory.objects.filter(id=id).first()
        student_category_name = student_category_name.category_name
        update = StudentCategory.objects.filter(id=id).update(status_code=0)
        if update:
            messages.success(request, f'{student_category_name} - Student Category has been deleted.')
            return JsonResponse({"status":"Deleted"})
        else:
            messages.error(request, f'Failed to delete Student Category - {student_category_name}')
            return JsonResponse({"status":"Not Deleted"})

     
#Process_Applications1 - Application List
@method_decorator(login_required, name='dispatch')
class ProcessApplications1(View):
    def get(self, request, *args, **kwargs):
        action = request.GET.get('action',None)
        category = request.GET.get('category',None)
        table_name = request.GET.get('table_name',None)         # Table name from AJAX
        id = request.GET.get('id',None)                         # id of specific record for update status_value from AJAx
        talukas = TypeMaster.objects.filter(category = "type_taluka").all()
        districts = TypeMaster.objects.filter(category = "type_district").all()
        
        # forms type
        form_types = TypeMaster.objects.filter(status_code=1,category = "form_type").all()
        # Forms name
        form_name = TypeMaster.objects.filter(Q(status_code=1) & Q(category = "form_type") & Q(name = table_name)).first()
        # Forms Status
        form_status = TypeMaster.objects.filter(status_code=1,category="form_status").all().order_by('sequence')
        
        # Get current year id from session.
        current_year_id = schSession.objects.get(is_default = True)
        try:
            # Fetching Specific Model Object
            model = apps.get_model('sat_application',table_name)
        except Exception as e:
            print(str(e))

        if action == "get_table_data":
            # Selected Filters value String
            status_value = request.GET.get('status',None)
            
            get_data = None
            if status_value != "":
                # List of selected status values 
                status_value = str(status_value).split(",")
                length = len(status_value)
                status_value = status_value[:length-1]
                
                # Table data of specific category and filters
                get_data = model.objects.filter(status_code=1,student_category_id = int(category),text_field_1__in = status_value,sch_session_id = current_year_id.id).all().values()

            # Dict of {status_name: count(status_name)}
            display_count = {}

            for i in form_status:
                print(i.name)
                # Adding Count of status in display_count dict
                display_count[i.name] = model.objects.filter(status_code=1,student_category_id = int(category),text_field_1 = i.name,sch_session_id = current_year_id.id).all().count()
            
            # Total number of students in studentcategory
            no_of_student_category = StudentCategory.objects.filter(status_code=1,id = category).first()
            total_no_of_student = no_of_student_category.no_of_candidates

            # Count of Total shortlisted student
            no_of_student = display_count["Shortlisted"]
            
            context = {
                'page_obj': get_data,       # table data
                'form_status': form_status,     # Forms Status - Shortlisted,Rejected etc..
                'no_of_student':str(no_of_student),         
                'form_name':str(form_name.description),         
                'total_no_of_student':str(total_no_of_student),
                'display_count':display_count,          # All Status Count 
                'db_table_name':table_name,             # Model name
                'districts':districts,
                'talukas':talukas
            }
            return render(request, 'table_view1.html', context)
           
        elif action == "get_category":
            print(action)
            parent_id = request.GET.get('parent_id',None) # Forms name
            print("parent_id:-",parent_id)
            if parent_id:
                process_data = StudentCategory.objects.filter(status_code=1,application_type = parent_id,student_category_session = current_year_id.id).values('id','application_type','category_name','courses_link','no_of_candidates')
                # List of Student Category
                list_process_data = list(process_data)
                print(process_data)
                return JsonResponse(list_process_data, safe=False)

        # For Form Status
        elif action == 'form_status':
            print(id)            
            update_status_value = request.GET.get('status_value')
            # status updating in Specific form
            update_status = model.objects.filter(id = id).update(text_field_1=update_status_value)
            
            # Selected Status value String
            status_value = request.GET.get('status',None)
            get_data = None
            if status_value != "":
                # Selected Status value List
                status_value = str(status_value).split(",")
                length = len(status_value)
                status_value = status_value[:length-1]
                
                print("Category",status_value)
                # Table data of specific category and filters
                get_data = model.objects.filter(status_code=1,student_category_id = int(category),text_field_1__in = status_value,sch_session_id = current_year_id.id).all().values()

            # Dict of {status_name: count(status_name)}
            display_count = {}              
            for i in form_status:
                print(i.name)
                display_count[i.name] = model.objects.filter(status_code=1,student_category_id = int(category),text_field_1 = i.name,sch_session_id = current_year_id.id).all().count()
            
            # Total number of students in studentcategory
            no_of_student_category = StudentCategory.objects.filter(status_code=1,id = category).first()
            total_no_of_student = no_of_student_category.no_of_candidates

            # Count of Total shortlisted student
            no_of_student = display_count["Shortlisted"]
            context = {
                'page_obj': get_data,       # table data
                'form_status': form_status,     # Forms Status - Shortlisted,Rejected etc..
                'no_of_student':str(no_of_student),         
                'form_name':str(form_name.description),         
                'total_no_of_student':str(total_no_of_student),
                'display_count':display_count,          # All Status Count 
                'db_table_name':table_name,             # Model name
                'status':'Updated',
                'msg': update_status_value,
                'districts':districts,
                'talukas':talukas
            }
            
            if update_status:
                return render(request, 'table_view1.html', context)
            else:
                context['status'] = 'Not updated'
                context['msg'] = update_status_value
                return render(request, 'table_view1.html', context)

        else:
            context = {
                    'form_types':form_types,
                    "redirect":"process_applications",
                    "form_status":form_status   
                }
            return render(request,'table_process_applications_1.html',context)


#Process_Applications2 - Shortlisted List
@method_decorator(login_required, name='dispatch')        
class ProcessApplications2(View):
    def get(self, request, *args, **kwargs):
        action = request.GET.get('action',None)
        category = request.GET.get('category',None)
        table_name = request.GET.get('table_name',None)         # Table name from AJAX
        id = request.GET.get('id',None)                         # id of specific record for update status_value from AJAx
        talukas = TypeMaster.objects.filter(category = "type_taluka").all()
        districts = TypeMaster.objects.filter(category = "type_district").all()
        
        # forms type
        form_types = TypeMaster.objects.filter(status_code=1,category = "form_type").all()
        # Forms name
        form_name = TypeMaster.objects.filter(Q(status_code=1) & Q(category = "form_type") & Q(name = table_name)).first()
        # Forms Status
        form_status = TypeMaster.objects.filter(status_code=1,category="form_status_select").all().order_by('sequence')
        
        # Get current year id from session.
        current_year_id = schSession.objects.get(is_default = True)
        try:
            # Fetching Specific Model Object
            model = apps.get_model('sat_application',table_name)
        except Exception as e:
            print(str(e))

        if action == "get_table_data":
            # Selected Filters value String
            status_value = request.GET.get('status',None)
            
            get_data = None
            if status_value != "":
                # List of selected status values 
                status_value = str(status_value).split(",")
                length = len(status_value)
                status_value = status_value[:length-1]    
                
                # Table data of specific category and filters
                get_data = model.objects.filter(status_code=1,student_category_id = int(category),text_field_1 = "Shortlisted",text_field_2__in = status_value,sch_session_id = current_year_id.id).all().values()

            # Dict of {status_name: count(status_name)}
            display_count = {}  
        
            for i in form_status:
                print(i.name)
                # Adding Count of status in display_count dict
                display_count[i.name] = model.objects.filter(status_code=1,student_category_id = int(category),text_field_2 = i.name,text_field_1 = "Shortlisted",sch_session_id = current_year_id.id).all().count()

            # Total Number of students in studentcategory
            no_of_student_category = StudentCategory.objects.filter(status_code=1,id = category).first()
            total_no_of_student = no_of_student_category.no_of_candidates

            # Count of Total Selected student
            no_of_student = display_count["Selected"]
            context = {
                'page_obj': get_data,       # table data
                'form_status': form_status,     # Forms Status - Shortlisted,Rejected etc..
                'no_of_student':str(no_of_student),         
                'form_name':str(form_name.description),         
                'total_no_of_student':str(total_no_of_student),
                'display_count':display_count,          # All Status Count 
                'db_table_name':table_name,             # Model name
                'districts':districts,
                'talukas':talukas
            }
            return render(request, 'table_view2.html', context)
           
        elif action == "get_category":
            print(action)
            parent_id = request.GET.get('parent_id',None) # Forms name
            print("parent_id:-",parent_id)
            if parent_id:
                process_data = StudentCategory.objects.filter(status_code=1,application_type = parent_id,student_category_session = current_year_id.id).values('id','application_type','category_name','courses_link','no_of_candidates')
                # List of Student Category
                list_process_data = list(process_data)
                print(process_data)
                return JsonResponse(list_process_data, safe=False)
  
        # For Form Status
        elif action == 'form_status':
            print(id)            
            update_status_value = request.GET.get('status_value')
            # status updating in Specific form
            update_status = model.objects.filter(id = id).update(text_field_2=update_status_value)

            # Selected Status value String
            status_value = request.GET.get('status',None)
            
            get_data = None
            if status_value != "":
                # Selected Status value List
                status_value = str(status_value).split(",")
                length = len(status_value)
                status_value = status_value[:length-1]
                
                print("Category",status_value)

                # Table data of specific category and filters
                get_data = model.objects.filter(status_code=1,student_category_id = int(category),text_field_1 = "Shortlisted",text_field_2__in = status_value,sch_session_id = current_year_id.id).all().values()

            # Dict of {status_name : count(status_name)}
            display_count = {}
            for i in form_status:
                print(i.name)
                display_count[i.name] = model.objects.filter(status_code=1,student_category_id = int(category),text_field_2 = i.name,text_field_1 = "Shortlisted",sch_session_id = current_year_id.id).all().count()
            
            # Total number of students in studentcategory
            no_of_student_category = StudentCategory.objects.filter(status_code=1,id = category).first()
            total_no_of_student = no_of_student_category.no_of_candidates

            # Count of Total shortlisted student
            no_of_student = display_count["Selected"]
            context = {
                'page_obj': get_data,       # table data
                'form_status': form_status,     # Forms Status - Shortlisted,Rejected etc..
                'no_of_student':str(no_of_student),         
                'form_name':str(form_name.description),         
                'total_no_of_student':str(total_no_of_student),
                'display_count':display_count,          # All Status Count 
                'db_table_name':table_name,             # Model name
                'status':'Updated',
                'msg': update_status_value,
                'districts':districts,
                'talukas':talukas
            }
            
            if update_status:
                return render(request, 'table_view2.html', context)
            else:
                context['status'] = 'Not updated'
                context['msg'] = update_status_value
                return render(request, 'table_view2.html', context)

        else:
            context = {
                    'form_types':form_types,
                    "redirect":"process_applications",
                    "form_status":form_status
                }
            return render(request,'table_process_applications_2.html',context)


#Process_Applications3 - Selected List
@method_decorator(login_required, name='dispatch')        
class ProcessApplications3(View):
    def get(self, request, *args, **kwargs):
        action = request.GET.get('action',None)
        category = request.GET.get('category',None)
        table_name = request.GET.get('table_name',None)         # Table name from AJAX
        id = request.GET.get('id',None)                         # id of specific record for update status_value from AJAx
        talukas = TypeMaster.objects.filter(category = "type_taluka").all()
        districts = TypeMaster.objects.filter(category = "type_district").all()
        
        # forms type
        form_types = TypeMaster.objects.filter(status_code=1,category = "form_type").all()
        # Forms name
        form_name = TypeMaster.objects.filter(Q(status_code=1) & Q(category = "form_type") & Q(name = table_name)).first()
        # Forms Status
        form_status = TypeMaster.objects.filter(status_code=1,category="form_status_recieved").all().order_by('sequence')
        
        # Get current year id from session.
        current_year_id = schSession.objects.get(is_default = True)
        try:
            # Fetching Specific Model Object
            model = apps.get_model('sat_application',table_name)
        except Exception as e:
            print(str(e))

        if action == "get_table_data":
            # Selected Filters value String
            status_value = request.GET.get('status',None)
            
            get_data = None
            if status_value != "":
                # List of selected status values 
                status_value = str(status_value).split(",")
                length = len(status_value)
                status_value = status_value[:length-1]    
                
                # Table data of specific category and filters
                get_data = model.objects.filter(status_code=1,student_category_id = int(category),text_field_2 = "Selected",text_field_3__in = status_value,sch_session_id = current_year_id.id).all().values()
   
            # Dict of {status_name: count(status_name)}
            display_count = {}  
        
            for i in form_status:
                print(i.name)
                # Adding Count of status in display_count dict
                display_count[i.name] = model.objects.filter(status_code=1,student_category_id = int(category),text_field_3 = i.name,text_field_2 = "Selected",sch_session_id = current_year_id.id).all().count()

            # Total Number of students in studentcategory
            no_of_student_category = StudentCategory.objects.filter(status_code=1,id = category).first()
            total_no_of_student = no_of_student_category.no_of_candidates

            context = {
                'page_obj': get_data,       # table data
                'form_status': form_status,     # Forms Status - Shortlisted,Rejected etc..
                'form_name':str(form_name.description),         
                'total_no_of_student':str(total_no_of_student),
                'display_count':display_count,          # All Status Count 
                'db_table_name':table_name,             # Model name
                'districts':districts,
                'talukas':talukas
            }
            return render(request, 'table_view3.html', context)
           
        elif action == "get_category":
            print(action)
            parent_id = request.GET.get('parent_id',None) # Forms name
            print("parent_id:-",parent_id)
            if parent_id:
                process_data = StudentCategory.objects.filter(status_code=1,application_type = parent_id,student_category_session = current_year_id.id).values('id','application_type','category_name','courses_link','no_of_candidates')
                # List of Student Category
                list_process_data = list(process_data)
                print(process_data)
                return JsonResponse(list_process_data, safe=False)

        # For Form Status
        elif action == 'form_status':
            print(id)            
            update_status_value = request.GET.get('status_value')
            # status updating in Specific form
            update_status = model.objects.filter(id = id).update(text_field_3=update_status_value)

            # Selected Status value String
            status_value = request.GET.get('status',None)
            
            get_data = None
            if status_value != "":
                # Selected Status value List
                status_value = str(status_value).split(",")
                length = len(status_value)
                status_value = status_value[:length-1]
                
                print("Category",status_value)
                # Table data of specific category and filters
                get_data = model.objects.filter(status_code=1,student_category_id = int(category),text_field_2 = "Selected",text_field_3__in = status_value,sch_session_id = current_year_id.id).all().values()

            # Dict of {status_name: count(status_name)}
            display_count = {}
            for i in form_status:
                print(i.name)
                display_count[i.name] = model.objects.filter(status_code=1,student_category_id = int(category),text_field_3 = i.name,text_field_2 = "Selected",sch_session_id = current_year_id.id).all().count()
            
            # Total number of students in studentcategory
            no_of_student_category = StudentCategory.objects.filter(status_code=1,id = category).first()
            total_no_of_student = no_of_student_category.no_of_candidates

            context = {
                'page_obj': get_data,       # table data
                'form_status': form_status,     # Forms Status - Shortlisted,Rejected etc..
                'form_name':str(form_name.description),         
                'total_no_of_student':str(total_no_of_student),
                'display_count':display_count,          # All Status Count 
                'db_table_name':table_name,             # Model name
                'status':'Updated',
                'msg': update_status_value,
                'districts':districts,
                'talukas':talukas
            }
            
            if update_status:
                return render(request, 'table_view3.html', context)
            else:
                context['status'] = 'Not updated'
                context['msg'] = update_status_value
                return render(request, 'table_view3.html', context)

        else:
            context = {
                    'form_types':form_types,
                    "redirect":"process_applications",
                    "form_status":form_status
                }
            return render(request,'table_process_applications_3.html',context)


#View_Application      
@method_decorator(login_required, name='dispatch')
class ViewApplication(View):
    def get(self, request, *args, **kwargs):
        form_name = request.GET.get('form_name',None)
        table_name = request.GET.get('table_name',None)         # Table name from AJAX
        id = request.GET.get('id',None)
        print("ID", id)

        # Get Model Object
        model = apps.get_model('sat_application',table_name)
        form_saved_data = model.objects.filter(id=id).first()

        talukas = TypeMaster.objects.filter(status_code=1,category = "type_taluka").all()
        districts = TypeMaster.objects.filter(status_code=1,category = "type_district").all()
        current_education_type = TypeMaster.objects.filter(status_code=1,category = "current_education_type").all().order_by('sequence')
        passed_education_type = TypeMaster.objects.filter(status_code=1,category = "passed_education_type").all().order_by('sequence')
        session_data = schSession.objects.all()

        # Template from TypeMaster
        application_type = TypeMaster.objects.filter(status_code=1,category = "application_type", name = form_name).first()
        template_name = str(application_type.description)
        print("template_name:-",template_name)
        District_id = form_saved_data.district
        print("District_id:",District_id)
        context = {
            'form_name':form_name,
            'form_saved_data':form_saved_data,
            'session_data':session_data,
            "talukas":talukas,
            "districts":districts,
            "current_education_type":current_education_type,
            "passed_education_type":passed_education_type,
            "District_id":int(District_id)
        }
        
        # try:
        #     user_data = UserDetails.objects.filter(user_id=id).first()
        #     context['user_data']=user_data
        
        # except:
        #     date_organization_started = form_saved_data.organization_started.strftime('%Y-%m-%d') if form_saved_data.organization_started else ''
        #     context['date_organization_started'] = date_organization_started

        try:
            date_organization_started = form_saved_data.organization_started.strftime('%Y-%m-%d') if form_saved_data.organization_started else ''
            context['date_organization_started'] = date_organization_started
            
            user_data = UserDetails.objects.filter(user_id=id).first()
            context['user_data']=user_data
            
        except:
            user_data = UserDetails.objects.filter(user_id=id).first()
            context['user_data']=user_data
            
            # date_organization_started = form_saved_data.organization_started.strftime('%Y-%m-%d') if form_saved_data.organization_started else ''
            # context['date_organization_started'] = date_organization_started
        
        return render(request,template_name,context)


#Uncategory_Applications
@method_decorator(login_required, name='dispatch')
class UncategoryApplications(View):
    def get(self, request, *args, **kwargs):
        action = request.GET.get('action',None)
        table_name = request.GET.get('table_name',None)         # Table name from AJAX
        id = request.GET.get('id',None)                         # id for update status_value from AJAx
        
        # forms type
        form_types = TypeMaster.objects.filter(status_code=1,category = "form_type").all()[:2]
        # Forms name
        form_name = TypeMaster.objects.filter(Q(status_code=1) & Q(category = "form_type") & Q(name = table_name)).first()
        # Forms Status
        form_status = TypeMaster.objects.filter(status_code=1,category="form_status").all().order_by('sequence')
        
        # Get current year id from session.
        current_year_id = schSession.objects.get(is_default = True)
        try:
            # Fetching Specific Model Object
            model = apps.get_model('sat_application',table_name)
        except Exception as e:
            print(str(e))

        if action == "get_table_data":
            application_form_name = request.GET.get('form_name',None)  
            print("application_form_name:-",application_form_name)            

            student_category = StudentCategory.objects.all()
            category_id_list = []
            for i in student_category:
                category_id_list.append(i.id)
            
            # Table data of specific category and filters
            get_data = model.objects.filter(status_code=1,sch_session_id = current_year_id.id).all().exclude(student_category_id__in = category_id_list)
            # Forms Status
            form_status = TypeMaster.objects.filter(status_code=1,category="form_status").all().order_by('sequence')

            # Dict of {status_name:count(status_name)}
            display_count = {}
            for i in form_status:
                print(i.name)
                # Adding Count of status in display_count dict
                display_count[i.name] = model.objects.filter(status_code=1,text_field_1 = i.name,sch_session_id = current_year_id.id).exclude(student_category_id__in = category_id_list).all().count()

            # Total number of students in studentcategory
            no_of_student = get_data.count() - display_count['Shortlisted']
            total_no_of_student = get_data.count()

            # Student category
            student_category_data = StudentCategory.objects.filter(status_code=1,application_type = application_form_name,student_category_session = current_year_id.id).all().values('id','application_type','category_name','courses_link','no_of_candidates')
           
           
            context = {
                'page_obj': get_data,       # table data
                'no_of_student':str(no_of_student),         
                'form_name':str(form_name.description),         
                'total_no_of_student':str(total_no_of_student),
                'display_count':display_count,          # All Status Count 
                'db_table_name':table_name,             # Model name
                'student_category_data':student_category_data
            }
            return render(request, 'table_view_uncategory_applications.html', context)
           
        elif action == "get_category":
            print(action)
            parent_id = request.GET.get('parent_id',None) # Forms name
            print("parent_id:-",parent_id)
            if parent_id:
                process_data = StudentCategory.objects.filter(status_code=1,application_type = parent_id,student_category_session = current_year_id.id).values('id','application_type','category_name','courses_link','no_of_candidates')
                # List of Student Category
                list_process_data = list(process_data)
                print(process_data)
                return JsonResponse(list_process_data, safe=False)

       
        # For Form Status
        if action == 'form_status':
            print(id)            
            category_status_value = request.GET.get('category_id',None)
            category_status_name = request.GET.get('category_status_value',None)
            # status updating in Specific form
            update_status = model.objects.filter(id = id).update(student_category=category_status_value)
            
            if update_status:
                return JsonResponse({'status':'Updated','msg': category_status_name})
            else:
                return JsonResponse({'status':'Not updated','msg': category_status_name })

        else:
            context = {
                'form_types':form_types,
                "redirect":"process_applications",
                "form_status":form_status
                    
                }
            return render(request,'table_uncategory_applications.html',context)


#ReportQuery
@method_decorator(login_required, name='dispatch')
class ReportQuery(View):
    def get(self,request,*args,**kwargs):
        
        action = request.GET.get('action', None)
        report_id = int(self.kwargs.get('id'))
        scholarship_form = StSchFormDetails.objects.filter(status_code=1).all()
        loan_form = StLoanFormDetails.objects.filter(status_code=1).all()
        vachanalay_form = VachnalayaForm.objects.filter(status_code=1).all()
        school_form = SchoolForm.objects.filter(status_code=1).all()
        anganwadi_form = AnganwadiForm.objects.filter(status_code=1).all()
        institution_form = InstitutionForm.objects.filter(status_code=1).all()
        districts = TypeMaster.objects.filter(category = "type_district").all()
        form_types = TypeMaster.objects.filter(status_code=1,category = "form_type").all()

        current_year_id = schSession.objects.get(year = (datetime.now().strftime('%Y')))

        if action == "get_category":
            print(action)
            parent_id = request.GET.get('parent_id',None) # Forms name

            if parent_id:
                process_data = StudentCategory.objects.filter(status_code=1,application_type = parent_id).values('id','application_type','category_name','courses_link','no_of_candidates')
                # List of Student Category
                list_process_data = list(process_data)
                print(process_data)
                return JsonResponse(list_process_data, safe=False)

        try:
            report_details = ReportManagement.objects.get(id=int(report_id))
            print("report_details", report_details)

        except:
            return HttpResponse("Please contact admin1")


        primary_filters = report_details.filters_list.all()
        print("primary_filters", primary_filters)
        
        secondary_filters = {
            "scholarship_form":["Scholarship Form",scholarship_form], "loan_form":["Student Loan Form",loan_form], 
            "vachanalay_form":["Vachanalay Form",vachanalay_form], "school_form":["School Form",school_form],
            "anganwadi_form":["Anganwadi Form",anganwadi_form], "institution_form":["Institution Form",institution_form],
            "districts":["Districts", districts]
            } 
        

        context = {"is_table":False, "report_details": report_details,
                    "primary_filters":primary_filters, "secondary_filters":secondary_filters,
                    "form_types":form_types, "districts":districts, "current_year_id":current_year_id}

        return render(request, 'reports_preview.html',context)      


    def post(self, request, *args, **kwargs):
        print(self.kwargs.get('id'))
        report_id = int(self.kwargs.get('id'))

        data = request.POST

        print(data)

        duration = data.get('duration')
        action = data.get('action')
        export = data.get('export')
        
        today = date.today()
        
        if duration == 'week':
            start_date, end_date = get_last_week_dates()
        elif duration == 'month':
            last_month, last_year = get_last_month_and_year()
            start_date, end_date = get_days_in_month(last_month, last_year)

        elif duration == 'quarter':
            last_month, last_year = get_last_month_and_year()
            start_date_last_month, end_date_last_month = get_days_in_month(last_month, last_year)

            days = get_last_four_months_days(3)

            start_date_last_quarter = start_date_last_month - timedelta(days=days)

            start_date = start_date_last_quarter
            end_date = end_date_last_month

        elif duration == 'half_yearly':
            last_month, last_year = get_last_month_and_year()
            start_date_last_month, end_date_last_month = get_days_in_month(last_month, last_year)

            days = get_last_four_months_days(6)

            start_date_last_quarter = start_date_last_month - timedelta(days=days)

            start_date = start_date_last_quarter
            end_date = end_date_last_month

        elif duration == 'yearly':
            today = date.today()
            last_year = today.year() - 1

            start_date = date(last_year, 1, 1)
            end_date = date(last_year, 31, 12)
            
        elif duration == 'custom':
            start_date_raw = data.get('start_date')
            end_date_raw = data.get('end_date')
            format = "%Y-%m-%d"

            start_date = datetime.strptime(start_date_raw, format)
            end_date = datetime.strptime(end_date_raw, format)


        try:    
            report_data = ReportManagement.objects.get(id=report_id)
            print("report_data", report_data)
        
        except:
            return HttpResponse("Please contact admin2") 
        
        query = report_data.query
        query = str(query)
        print("query",query)

        filters_list = report_data.filters_list.all()
        print("filters_list", filters_list)

        where_clause = ""
        filter_data = data.getlist('primary_filters')
        print("filter_data")

        for filters in filters_list:
            print("FILTERS")
            if filters.db_name in filter_data:
                where_clause = where_clause + f"{filters.query_string}"         
                
                for filter_data in filter_data:
                    filter_values_list = data.getlist(f'secondary_filters_{filters.db_name}')
                    if filters.is_id == 0:
                        filter_values_string = ', '.join(['"'+ item.split('_')[1] +'"' for item in filter_values_list])
                    elif filters.is_id == 1:
                        filter_values_string = ', '.join(['"'+ item.split('_')[0] +'"' for item in filter_values_list])
                    
                if where_clause:
                    where_clause = where_clause + " and "
                    where_clause = where_clause.replace(filters.replacable_variable, f"({filter_values_string})")            
                else:
                    where_clause = where_clause.replace(filters.replacable_variable, f"({filter_values_string})")            


        if duration == 'all':
            duration = f"LIKE ('%')"
            message = f"Displaying data for all records"

        else:
            query_start_date = start_date.strftime("%Y-%m-%d")
            query_end_date = end_date.strftime("%Y-%m-%d")
            duration = f"BETWEEN '{query_start_date}' AND '{query_end_date}'"   
            message = f"Displaying data from {query_start_date} to {query_end_date}"


        query = query.replace("$DURATION",duration)
        if where_clause:
            query = query.replace("$WHERECLAUSE",where_clause)
        else:
            query = query.replace("$WHERECLAUSE","")

        print(query) 

        with connection.cursor() as cursor:
            cursor.execute(query)
            print("Component after query")
            try:
                data = cursor.fetchall()         
                header = [desc for desc in cursor.description]
            except Exception as ex:
                messages.error(request, (f'Incorrect Query {ex}'))
                return redirect('report-data-table', id=report_id)  
        
        # try:
        #     mycursor = connection.cursor()
        #     mycursor.execute(query) 
        #     data = mycursor.fetchall()         
        #     header = mycursor.description
        # except Exception as ex:
        #     messages.error(request, (f'Incorrect Query {ex}'))
        #     return redirect('report-data-table', id=report_id)
        

        table_headers = [field_name[0] for field_name in header[int(report_data.columns_to_skip):]]
        print("table_headers",table_headers)

        table_data = []
        # table_data.append(table_headers)
        print("table_data", table_data)

        for x in data:
            fields = list(x[int(report_data.columns_to_skip):])

            table_data.append(fields) 

        jsonStr = json.dumps(table_data,default=json_serial)
        
        print("EXPORT")
        if action == "export" and export == 'csv':
    
            final_data = [table_headers] + table_data
            print("final_data", final_data)

            path = generate_and_save_json(final_data, request.user.username)    
            
            file = open(path, "r")
            
            # Sending request to elorca reports -----------------------------------------------
            import requests

            url = "https://reports.elorca.com/"

            payload={
                "token": "b2f11f01d535ea901a4e41da544f827460ce0dd3"
                }
            files=[
            ('json',('report_json.json',open(path,'rb'),'application/json'))
            ]
            headers = {
            'Content-Type': 'application/json',
            'Content-Type': 'application/octet-stream'
            }

            response_report = requests.request("POST", url, data=payload, files=files)


            file_url = response_report.text

            # Make the HTTP request to fetch the file
            response = requests.get(file_url)

            # Check if the request was successful
            if response.status_code == 200:
                # Create a FileResponse instance with the fetched file
                file_response = FileResponse(response)
                print(file_response)
                # Set the content type (optional)
                file_response["Content-Type"] = "application/octet-stream"

                # Set the file name for download (optional)
                file_response["Content-Disposition"] = "attachment; filename=report.csv"

                return file_response
            else:
                # Return an appropriate error response if the request fails
                return HttpResponse("Failed to fetch the file.", status=response.status_code)

            # --------------------------------------------------------------------------------

        
        elif action == "export" and export == 'xlsx':
            print("Enter in action export")
            workbook = Workbook()

            # Get the active worksheet
            worksheet = workbook.active

            # Example data list
            data_list = final_data = [table_headers] + table_data
            print("data_list", data_list)
            # Write data to the worksheet
            for row in data_list:
                worksheet.append(row)

            # Create a response object with the appropriate content type
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

            # Set the file name for download
            response['Content-Disposition'] = 'attachment; filename=report.xlsx'

            # Save the workbook to the response
            workbook.save(response)

            return response
        
        context = {
            "table_data":table_data,
            "new_data":jsonStr,
            "table_headers":table_headers,
            "is_table":True,
            "message": message,

        }          
        cursor.close()
        # mycursor.close()

        return render(request, 'reports_preview.html',context)


#Dashboard
@method_decorator(login_required, name='dispatch')
class Dashboard(View):
    def get(self, request, *args, **kwargs):
        action = request.GET.get('action',None)
        # Forms Types - Name
        form_types = TypeMaster.objects.filter(status_code=1,category = "form_type").all()
        # All Register USer
        register_user = UserDetails.objects.all().count()
        
        # Get current year id from session.
        current_year_id = schSession.objects.get(is_default = True)
        # Initial Count
        Draft,Selected,Rejected = 0,0,0
        for forms in form_types:
            # Table name - string
            table_name = forms.name
            # Get Model
            model = apps.get_model('sat_application',table_name)
            # Filter All Data
            # new_draft = model.objects.filter(status_code=1,text_field_1 = "Draft",sch_session_id = current_year_id.id).all().count()
            new_draft = model.objects.filter(status_code=1,sch_session_id = current_year_id.id).all().count()
            new_selected = model.objects.filter(status_code=1,text_field_2 = "Selected",sch_session_id = current_year_id.id).all().count()
            new_rejected_phase2 = model.objects.filter(status_code=1,text_field_2 = "Rejected",sch_session_id = current_year_id.id).all().count()
            new_rejected = new_rejected_phase2
            print("new_draft:-",new_draft,"new_selected:-",new_selected,"new_rejected:-",new_rejected)
            
            # Total Count
            Draft = Draft + new_draft   # Form Submitted Count
            Selected = Selected + new_selected
            Rejected = Rejected + new_rejected

        print("Draft:-",Draft,"Selected:-",Selected,"Rejected:-",Rejected,"register_user:-",register_user)

        if action == "get_shortlisted_data":
            form_name = request.GET.get('form_name',None)
            table_name_db = request.GET.get('table_name',None)
            print("form_name:-",form_name)
            # Student category names
            student_category = StudentCategory.objects.filter(status_code=1,application_type = form_name,student_category_session = current_year_id.id).all()
            if len(student_category)>=1:
                print("Category")
                category_wise_shortlisted_count = []
                for category in student_category:
                    category_id = category.id
                    category_name = category.category_name
                    no_of_candidates = category.no_of_candidates

                    model = apps.get_model('sat_application',table_name_db)
                    # Shortlisted count from specific table
                    shortlisted_count = model.objects.filter(status_code=1,student_category = category_id,sch_session_id = current_year_id.id).filter(text_field_1 = "Shortlisted").count()
                    
                    # Percentage 
                    percentage_count = (shortlisted_count / no_of_candidates) * 100
                    total_shortlisted_count = str(shortlisted_count) + "/" + str(no_of_candidates)
                    
                    data = {
                        'category_name':category_name,
                        'no_of_candidates':no_of_candidates,
                        'shortlisted_count':shortlisted_count,
                        'percentage_count':percentage_count,
                        'total_shortlisted_count':total_shortlisted_count
                    }
                    category_wise_shortlisted_count.append(data)
                    data = [category_wise_shortlisted_count,form_name]
                print("DATA:-",data)
            else:
                data = ["",form_name]
            return JsonResponse(data, safe=False)
        

        if action == "get_selected_data":
            form_name = request.GET.get('form_name',None)       # Form name
            table_name_db = request.GET.get('table_name',None)      # Db Model name
            
            # Student category names
            student_category = StudentCategory.objects.filter(status_code=1,application_type = form_name,student_category_session = current_year_id.id).all()
            if len(student_category)>=1:
                category_wise_shortlisted_count = []
                # Student category of specific form
                for category in student_category:
                    category_id = category.id
                    category_name = category.category_name
                    no_of_candidates = category.no_of_candidates

                    model = apps.get_model('sat_application',table_name_db)
                    # Shortlisted count from specific table
                    shortlisted_count = model.objects.filter(status_code=1,student_category = category_id,sch_session_id = current_year_id.id).filter(text_field_2 = "Selected",sch_session_id = current_year_id.id).count()
                    # Percentage 
                    percentage_count = (shortlisted_count / no_of_candidates) * 100
                    total_selected_count = str(shortlisted_count) + "/" + str(no_of_candidates)

                    data = {
                        'category_name':category_name,
                        'no_of_candidates':no_of_candidates,
                        'shortlisted_count':shortlisted_count,
                        'percentage_count':percentage_count,
                        'total_selected_count':total_selected_count
                    }
                    category_wise_shortlisted_count.append(data)
                    data = [category_wise_shortlisted_count,form_name]
            else:
                data = ["",form_name]
            return JsonResponse(data, safe=False)

        # Total Application count with {form name : count}
        total_applications_count_data = {}
        for i in form_types:
            model = apps.get_model('sat_application',i.name)
            total_applications_count = model.objects.filter(status_code = 1,sch_session_id = current_year_id.id).all().count()
            total_applications_count_data[i.description] = total_applications_count
        
        # Data and Labels for Chart js
        data = []
        labels = []
        for key,value in total_applications_count_data.items():
            labels.append(key)
            data.append(value)

        # doughnut chart background color
        chart_color_obj = TypeMaster.objects.filter(status_code=1,category = "doughnut_chart_color").all().order_by('sequence')
        chart_color = [color.name for color in chart_color_obj]

        textfield1_status_count = {}
        textfield1_card_status_obj = TypeMaster.objects.filter(status_code=1,category = "textfield1_card_status").all().order_by('sequence')
        for textfield1_status in textfield1_card_status_obj:
            total_applications_count = 0
            for form in form_types:
                model = apps.get_model('sat_application',form.name)
                total_applications_count += model.objects.filter(status_code = 1,sch_session_id = current_year_id.id,text_field_1 = textfield1_status.name).all().count()
            textfield1_status_count[textfield1_status.name] = total_applications_count
        
        textfield2_status_count = {}
        textfield2_card_status_obj = TypeMaster.objects.filter(status_code=1,category = "textfield2_card_status").all().order_by('sequence')
        for textfield2_status in textfield2_card_status_obj:
            total_applications_count2 = 0
            for form in form_types:
                model = apps.get_model('sat_application',form.name)
                total_applications_count2 += model.objects.filter(status_code = 1,sch_session_id = current_year_id.id,text_field_2 = textfield2_status.name).all().count()
            textfield2_status_count[textfield2_status.name] = total_applications_count2
        
        # textfield3_card_status
        textfield3_status_count = {}
        textfield3_card_status_obj = TypeMaster.objects.filter(status_code=1,category = "textfield3_card_status").all().order_by('sequence')
        for textfield3_status in textfield3_card_status_obj:
            total_applications_count3 = 0
            for form in form_types:
                model = apps.get_model('sat_application',form.name)
                total_applications_count3 += model.objects.filter(status_code = 1,sch_session_id = current_year_id.id,text_field_3 = textfield3_status.name).all().count()
            textfield3_status_count[textfield3_status.name] = total_applications_count3

        context = {
            'Draft':Draft,    # Form Submitted Count
            'Selected':Selected,
            'Rejected':Rejected,
            'register_user':register_user,
            'form_types':form_types,
            'total_applications_count_data':total_applications_count_data,
            'labels':labels,
            'data':data,
            'chart_color':chart_color,
            'textfield1_status_count':textfield1_status_count,
            'textfield2_status_count':textfield2_status_count,
            'textfield3_status_count':textfield3_status_count
        }
        return render(request,'sat_dashboard.html',context)



# ViewProcessApplications1 - Application View
@method_decorator(login_required, name='dispatch')
class ViewProcessApplications1(View):
    def get(self, request, *args, **kwargs):
        action = request.GET.get('action',None)
        category = request.GET.get('category',None)
        table_name = request.GET.get('table_name',None)         # Table name from AJAX
        id = request.GET.get('id',None)                         # id of specific record for update status_value from AJAx
        talukas = TypeMaster.objects.filter(category = "type_taluka").all()
        districts = TypeMaster.objects.filter(category = "type_district").all()
        
        # forms type
        form_types = TypeMaster.objects.filter(status_code=1,category = "form_type").all()
        # Forms name
        form_name = TypeMaster.objects.filter(Q(status_code=1) & Q(category = "form_type") & Q(name = table_name)).first()
        # Forms Status
        form_status = TypeMaster.objects.filter(status_code=1,category="form_status").all().order_by('sequence')
        
        # Get current year id from session.
        current_year_id = schSession.objects.get(is_default = True)
        try:
            # Fetching Specific Model Object
            model = apps.get_model('sat_application',table_name)
        except Exception as e:
            print(str(e))

        if action == "get_table_data":
            # Selected Filters value String
            status_value = request.GET.get('status',None)
            get_data = None
            if status_value != "":
                # List of selected status values 
                status_value = str(status_value).split(",")
                length = len(status_value)
                status_value = status_value[:length-1]
                
                # Table data of specific category and filters
                get_data = model.objects.filter(status_code=1,student_category_id = int(category),text_field_1__in = status_value,sch_session_id = current_year_id.id).all().values()
            
            # dict of - status : count of status
            display_count = {}

            for i in form_status:
                print(i.name)
                # Adding Count of status in display_count dict
                display_count[i.name] = model.objects.filter(status_code=1,student_category_id = int(category),text_field_1 = i.name,sch_session_id = current_year_id.id).all().count()
            
            # Total Number of students in studentcategory
            no_of_student_category = StudentCategory.objects.filter(status_code=1,id = category).first()
            total_no_of_student = no_of_student_category.no_of_candidates

            # Count of Total shortlisted student
            no_of_student = display_count["Shortlisted"]
            
            context = {
                'page_obj': get_data,       # table data
                'form_status': form_status,     # Forms Status - Shortlisted,Rejected etc..
                'no_of_student':str(no_of_student),         
                'form_name':str(form_name.description),         
                'total_no_of_student':str(total_no_of_student),
                'display_count':display_count,          # All Status Count 
                'db_table_name':table_name,             # Model name
                'districts':districts,
                'talukas':talukas
            }
            return render(request, 'view_table_process1.html', context)
           
        elif action == "get_category":
            print(action)
            parent_id = request.GET.get('parent_id',None) # Forms name
            print("parent_id:-",parent_id)
            if parent_id:
                process_data = StudentCategory.objects.filter(status_code=1,application_type = parent_id,student_category_session = current_year_id.id).values('id','application_type','category_name','courses_link','no_of_candidates')
                # List of Student Category
                list_process_data = list(process_data)
                print(process_data)
                return JsonResponse(list_process_data, safe=False)

        # For Form Status
        elif action == 'form_status':
            print(id)            
            update_status_value = request.GET.get('status_value')
            # status updating in Specific form
            update_status = model.objects.filter(id = id).update(text_field_1=update_status_value)
            
            # Selected Status value String
            status_value = request.GET.get('status',None)
            
            get_data = None
            if status_value != "":
                # Selected Status value List
                status_value = str(status_value).split(",")
                length = len(status_value)
                status_value = status_value[:length-1]
                
                print("Category",status_value)
                
                # Table data of specific category and filters
                get_data = model.objects.filter(status_code=1,student_category_id = int(category),text_field_1__in = status_value,sch_session_id = current_year_id.id).all().values()

            # Dict of {status_name : count(status_name)}
            display_count = {}
            for i in form_status:
                print(i.name)
                display_count[i.name] = model.objects.filter(status_code=1,student_category_id = int(category),text_field_1 = i.name,sch_session_id = current_year_id.id).all().count()
            
            # Total number of students in studentcategory
            no_of_student_category = StudentCategory.objects.filter(status_code=1,id = category).first()
            total_no_of_student = no_of_student_category.no_of_candidates

            # Count of Total shortlisted student
            no_of_student = display_count["Shortlisted"]
            context = {
                'page_obj': get_data,       # table data
                'form_status': form_status,     # Forms Status - Shortlisted,Rejected etc..
                'no_of_student':str(no_of_student),         
                'form_name':str(form_name.description),         
                'total_no_of_student':str(total_no_of_student),
                'display_count':display_count,          # All Status Count 
                'db_table_name':table_name,             # Model name
                'status':'Updated',
                'msg': update_status_value,
                'districts':districts,
                'talukas':talukas
            }
            
            if update_status:
                return render(request, 'view_table_process1.html', context)
            else:
                context['status'] = 'Not updated'
                context['msg'] = update_status_value
                return render(request, 'view_table_process1.html', context)
        
        else:
            context = {
                    'form_types':form_types,
                    "redirect":"process_applications",
                    "form_status":form_status   
                }
            return render(request,'view_process_application_1.html',context)


#ViewProcessApplications2 - Shortlisted View
@method_decorator(login_required, name='dispatch')        
class ViewProcessApplications2(View):
    def get(self, request, *args, **kwargs):
        action = request.GET.get('action',None)
        category = request.GET.get('category',None)
        table_name = request.GET.get('table_name',None)         # Table name from AJAX
        id = request.GET.get('id',None)                         # id of specific record for update status_value from AJAx
        talukas = TypeMaster.objects.filter(category = "type_taluka").all()
        districts = TypeMaster.objects.filter(category = "type_district").all()
        
        # forms type
        form_types = TypeMaster.objects.filter(status_code=1,category = "form_type").all()
        # Forms name
        form_name = TypeMaster.objects.filter(Q(status_code=1) & Q(category = "form_type") & Q(name = table_name)).first()
        # Forms Status
        form_status = TypeMaster.objects.filter(status_code=1,category="form_status_select").all().order_by('sequence')
        
        # Get current year id from session.
        current_year_id = schSession.objects.get(is_default = True)
        try:
            # Fetching Specific Model Object
            model = apps.get_model('sat_application',table_name)
        except Exception as e:
            print(str(e))

        if action == "get_table_data":
            # Selected Filters value String
            status_value = request.GET.get('status',None)
            
            get_data = None
            if status_value != "":
                # List of selected status values 
                status_value = str(status_value).split(",")
                length = len(status_value)
                status_value = status_value[:length-1]    
                
                # Table data of specific category and filters
                get_data = model.objects.filter(status_code=1,student_category_id = int(category),text_field_1 = "Shortlisted",text_field_2__in = status_value,sch_session_id = current_year_id.id).all().values()

            # dict of - status : count of status
            display_count = {}  
        
            for i in form_status:
                print(i.name)
                # Adding Count of status in display_count dict
                display_count[i.name] = model.objects.filter(status_code=1,student_category_id = int(category),text_field_2 = i.name,text_field_1 = "Shortlisted",sch_session_id = current_year_id.id).all().count()


            # Total Number of students in studentcategory
            no_of_student_category = StudentCategory.objects.filter(status_code=1,id = category).first()
            total_no_of_student = no_of_student_category.no_of_candidates

            # Count of Total shortlisted student
            no_of_student = display_count["Selected"]

            context = {
                'page_obj': get_data,       # table data
                'form_status': form_status,     # Forms Status - Shortlisted,Rejected etc..
                'no_of_student':str(no_of_student),         
                'form_name':str(form_name.description),         
                'total_no_of_student':str(total_no_of_student),
                'display_count':display_count,          # All Status Count 
                'db_table_name':table_name,             # Model name
                'districts':districts,
                'talukas':talukas
            }
            return render(request, 'view_table_process2.html', context)
           
        elif action == "get_category":
            print(action)
            parent_id = request.GET.get('parent_id',None) # Forms name
            print("parent_id:-",parent_id)
            if parent_id:
                process_data = StudentCategory.objects.filter(status_code=1,application_type = parent_id,student_category_session = current_year_id.id).values('id','application_type','category_name','courses_link','no_of_candidates')
                # List of Student Category
                list_process_data = list(process_data)
                print(process_data)
                return JsonResponse(list_process_data, safe=False)

        # For Form Status
        elif action == 'form_status':
            print(id)            
            update_status_value = request.GET.get('status_value')
            # status updating in Specific form           
            update_status = model.objects.filter(id = id).update(text_field_2=update_status_value)
            
            # Selected Status value String
            status_value = request.GET.get('status',None)
           
            get_data = None
            if status_value != "":
                # Selected Status value List
                status_value = str(status_value).split(",")
                length = len(status_value)
                status_value = status_value[:length-1]
                
                print("Category",status_value)
                
                # Table data of specific category and filters
                get_data = model.objects.filter(status_code=1,student_category_id = int(category),text_field_1 = "Shortlisted",text_field_2__in = status_value,sch_session_id = current_year_id.id).all().values()

            # Dict of {status_name : count(status_name)}
            display_count = {}
            for i in form_status:
                print(i.name)
                display_count[i.name] = model.objects.filter(status_code=1,student_category_id = int(category),text_field_2 = i.name,text_field_1 = "Shortlisted",sch_session_id = current_year_id.id).all().count()
            
            # Total number of students in studentcategory
            no_of_student_category = StudentCategory.objects.filter(status_code=1,id = category).first()
            total_no_of_student = no_of_student_category.no_of_candidates

            # Count of Total shortlisted student
            no_of_student = display_count["Selected"]
            context = {
                'page_obj': get_data,       # table data
                'form_status': form_status,     # Forms Status - Shortlisted,Rejected etc..
                'no_of_student':str(no_of_student),         
                'form_name':str(form_name.description),         
                'total_no_of_student':str(total_no_of_student),
                'display_count':display_count,          # All Status Count 
                'db_table_name':table_name,             # Model name
                'status':'Updated',
                'msg': update_status_value,
                'districts':districts,
                'talukas':talukas
            }
            
            if update_status:
                return render(request, 'view_table_process2.html', context)
            else:
                context['status'] = 'Not updated'
                context['msg'] = update_status_value
                return render(request, 'view_table_process2.html', context)

           
        else:
            context = {
                    'form_types':form_types,
                    "redirect":"process_applications",
                    "form_status":form_status
                }
            return render(request,'view_process_application_2.html',context)



#ViewProcessApplications3 - Selected View
@method_decorator(login_required, name='dispatch')        
class ViewProcessApplications3(View):
    def get(self, request, *args, **kwargs):
        action = request.GET.get('action',None)
        category = request.GET.get('category',None)
        table_name = request.GET.get('table_name',None)         # Table name from AJAX
        id = request.GET.get('id',None)                         # id of specific record for update status_value from AJAx
        talukas = TypeMaster.objects.filter(category = "type_taluka").all()
        districts = TypeMaster.objects.filter(category = "type_district").all()
        
        # forms type
        form_types = TypeMaster.objects.filter(status_code=1,category = "form_type").all()
        # Forms name
        form_name = TypeMaster.objects.filter(Q(status_code=1) & Q(category = "form_type") & Q(name = table_name)).first()
        # Forms Status
        form_status = TypeMaster.objects.filter(status_code=1,category="form_status_recieved").all().order_by('sequence')
        
        # Get current year id from session.
        current_year_id = schSession.objects.get(is_default = True)
        try:
            # Fetching Specific Model Object
            model = apps.get_model('sat_application',table_name)
        except Exception as e:
            print(str(e))

        if action == "get_table_data":
            # Selected Filters value String
            status_value = request.GET.get('status',None)
            
            get_data = None
            if status_value != "":
                # List of selected status values 
                status_value = str(status_value).split(",")
                length = len(status_value)
                status_value = status_value[:length-1]    

                # Table data of specific category and filters
                get_data = model.objects.filter(status_code=1,student_category_id = int(category),text_field_2 = "Selected",text_field_3__in = status_value,sch_session_id = current_year_id.id).all().values()

            # dict of - status : count of status
            display_count = {}  
        
            for i in form_status:
                print(i.name)
                # Adding Count of status in display_count dict
                display_count[i.name] = model.objects.filter(status_code=1,student_category_id = int(category),text_field_3 = i.name,text_field_2 = "Selected",sch_session_id = current_year_id.id).all().count()

            
            # Total Number of students in studentcategory
            no_of_student_category = StudentCategory.objects.filter(status_code=1,id = category).first()
            total_no_of_student = no_of_student_category.no_of_candidates

            context = {
                'page_obj': get_data,       # table data
                'form_status': form_status,     # Forms Status - Shortlisted,Rejected etc..
                'form_name':str(form_name.description),         
                'total_no_of_student':str(total_no_of_student),
                'display_count':display_count,          # All Status Count 
                'db_table_name':table_name,             # Model name
                'districts':districts,
                'talukas':talukas
            }
            return render(request, 'view_table_process3.html', context)
           
        elif action == "get_category":
            print(action)
            parent_id = request.GET.get('parent_id',None) # Forms name
            print("parent_id:-",parent_id)
            if parent_id:
                process_data = StudentCategory.objects.filter(status_code=1,application_type = parent_id,student_category_session = current_year_id.id).values('id','application_type','category_name','courses_link','no_of_candidates')
                # List of Student Category
                list_process_data = list(process_data)
                print(process_data)
                return JsonResponse(list_process_data, safe=False)

        
        # For Form Status
        elif action == 'form_status':
            print(id)            
            update_status_value = request.GET.get('status_value')
            # status updating in Specific form           
            update_status = model.objects.filter(id = id).update(text_field_3=update_status_value)
            
            # Selected Status value String
            status_value = request.GET.get('status',None)
            
            get_data = None
            if status_value != "":
                # Selected Status value List
                status_value = str(status_value).split(",")
                length = len(status_value)
                status_value = status_value[:length-1]
                
                print("Category",status_value)
               
                # Table data of specific category and filters
                get_data = model.objects.filter(status_code=1,student_category_id = int(category),text_field_2 = "Selected",text_field_3__in = status_value,sch_session_id = current_year_id.id).all().values()

            # Dict of {status_name:count(status_name)}
            display_count = {}
            for i in form_status:
                print(i.name)
                display_count[i.name] = model.objects.filter(status_code=1,student_category_id = int(category),text_field_3 = i.name,text_field_2 = "Selected",sch_session_id = current_year_id.id).all().count()
            
            # Total number of students in studentcategory
            no_of_student_category = StudentCategory.objects.filter(status_code=1,id = category).first()
            total_no_of_student = no_of_student_category.no_of_candidates

            context = {
                'page_obj': get_data,       # table data
                'form_status': form_status,     # Forms Status - Shortlisted,Rejected etc..
                'form_name':str(form_name.description),         
                'total_no_of_student':str(total_no_of_student),
                'display_count':display_count,          # All Status Count 
                'db_table_name':table_name,             # Model name
                'status':'Updated',
                'msg': update_status_value,
                'districts':districts,
                'talukas':talukas
            }
            
            if update_status:
                return render(request, 'view_table_process3.html', context)
            else:
                context['status'] = 'Not updated'
                context['msg'] = update_status_value
                return render(request, 'view_table_process3.html', context)
        else:
            context = {
                    'form_types':form_types,
                    "redirect":"process_applications",
                    "form_status":form_status
                }
            return render(request,'view_process_application_3.html',context)
