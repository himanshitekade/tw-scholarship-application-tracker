from django.db import models
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings

# Create your models here.
class ObjectManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status_code=1)


class Base(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="%(app_label)s_%(class)s_creator_name",null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="%(app_label)s_%(class)s_editor_name",null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    status_code = models.IntegerField(default=1)
    objects = ObjectManager()

    class Meta:
        abstract = True

class schSession(models.Model):
    year = models.CharField(max_length=100,null=True,blank=True)
    start_session = models.CharField(max_length=100,null=True,blank=True)
    end_session = models.CharField(max_length=100,null=True,blank=True)
    name_session = models.CharField(max_length=200,null=True,blank=True)
    comments = models.CharField(max_length=500,null=True,blank=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name_session


class Privileges(Base):
    name = models.CharField(max_length=100, null=True,blank=True)
    description = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name


class Roles(Base):
    name = models.CharField(max_length = 100)
    privileges = models.ManyToManyField(Privileges)


    def __str__(self):
        return self.name


class UserDetails(Base):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    role = models.ManyToManyField(Roles)
    mobile = PhoneNumberField(blank=False, null=False)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)

    


    def __str__(self):
         return self.user.email


class TypeMaster(Base):
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    parent_id = models.IntegerField(blank=True, null=True)
    display_flag = models.BooleanField(blank=True, null=True)
    sequence = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name



class StudentCategory(Base):
    category_name = models.CharField(max_length=100,blank=True, null=True)
    student_category_session = models.ForeignKey(schSession, on_delete = models.CASCADE)
    application_type = models.CharField(max_length=50,blank=True, null=True)
    no_of_candidates = models.IntegerField(blank=True, null=True)
    amt_for_candidates = models.FloatField(blank=True, null=True)
    courses_link = models.CharField(max_length=2000,blank=True, null=True)
    total_amt = models.FloatField(blank=True, null=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):

        return self.category_name


class StudentApplicant(Base):
    first_name = models.CharField(max_length=100, blank=False, null=False)
    middle_name = models.CharField(max_length=100, blank=False, null=False)
    last_name = models.CharField(max_length=100, blank=False, null=False)
    first_name_marathi = models.CharField(max_length=100, blank=False, null=False)
    middle_name_marathi = models.CharField(max_length=100, blank=False, null=False)
    last_name_marathi = models.CharField(max_length=100, blank=False, null=False)
    address = models.CharField(max_length=500, blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    email = models.EmailField(max_length=50,blank=False, null=False)
    mobile = PhoneNumberField(blank=False, null=False)
    district = models.CharField(max_length=100, blank=True, null=True)
    taluka = models.CharField(max_length=100, blank=True, null=True)
    mulgaon = models.CharField(max_length=100, blank=True, null=True)
    is_disablity_candidate = models.BooleanField(default=0, blank= True,null=True)
    disablity_certificate = models.FileField(upload_to='student_applicant',blank=True, null=True)
    aadhar_card = models.FileField(upload_to='aadhar_files', blank=True, null=True)
    address_proof = models.FileField(upload_to='address_proofs', blank=True, null=True)
    income_certificate = models.FileField(upload_to='income_certificates', blank=True, null=True)
    bonafide_certificate = models.FileField(upload_to='bonafide_certificates', blank=True, null=True)
    ration_card = models.FileField(upload_to='ration_cards', blank=True, null=True)
    passed_college_name = models.CharField(max_length=500, blank=True, null=True)
    passed_education = models.CharField(max_length=100, blank=True, null=True)
    passed_education_percentage = models.FloatField(blank=True, null=True)
    passed_education_marksheet = models.FileField(upload_to='form_details',blank=True, null=True)
    current_education = models.CharField(max_length=100, blank=True, null=True)
    is_application_received_previously = models.BooleanField(default=0,blank= True, null=True)
    college_distance = models.CharField(max_length=500,null=True,blank=True)
    college_travel_vehical = models.CharField(max_length=100,null=True,blank=True)
    college_expenditure_tohome = models.CharField(max_length=100,null=True,blank=True)
    family_details = models.CharField(max_length=1000,null=True,blank=True)
    family_income = models.CharField(max_length=1000,null=True,blank=True)
    tuition_fee = models.CharField(max_length=500,null=True,blank=True)
    cost_books = models.CharField(max_length=200,null=True,blank=True)
    cost_uniform = models.CharField(max_length=200,null=True,blank=True)
    academic_year_cost_travel = models.CharField(max_length=1000,null=True,blank=True)
    hostel_fees = models.CharField(max_length=300,null=True,blank=True)
    is_birth_place_different = models.BooleanField(default=0,blank= True, null=True)
    birth_place = models.CharField(max_length=100,null=True,blank=True)
    is_certificate_sports = models.BooleanField(default=0,blank= True, null=True)
    upload_certificate_sports = models.FileField(upload_to='sports_certificates', blank=True, null=True)
    is_alive = models.BooleanField(default=0,blank= True, null=True)
    upload_certificate_isalive = models.FileField(upload_to='isalive_certificates', blank=True, null=True)
    is_district_level_player = models.BooleanField(default=0, blank= True, null=True)
    upload_certificate_district_level = models.FileField(upload_to='district_level_certificates', blank=True, null=True)
    bank_name = models.CharField(max_length=200,null=True,blank=True)
    account_no = models.CharField(max_length=200,null=True,blank=True)
    account_holder = models.CharField(max_length=200,null=True,blank=True)
    branch_name = models.CharField(max_length=200,null=True,blank=True)
    ifsc_code = models.CharField(max_length=200,null=True,blank=True)
    other_passed_education = models.CharField(max_length=200, blank=True, null=True)
    other_current_education = models.CharField(max_length=200, blank=True, null=True)
    other_taluka = models.CharField(max_length=200, blank=True, null=True)
    other_district = models.CharField(max_length=200, blank=True, null=True)
    is_other_sch_received = models.BooleanField(default=0,blank= True, null=True)
    other_sch_received_amt = models.FloatField(blank=True, null=True)
    teacher_one = models.FileField(upload_to='teacher_one',blank=True, null=True)
    teacher_two = models.FileField(upload_to='teacher_two',blank=True, null=True)
    fee_receipt = models.FileField(upload_to='fee_receipt',blank=True, null=True)
    birth_other_taluka = models.CharField(max_length=200, blank=True, null=True)
    birth_other_district = models.CharField(max_length=200, blank=True, null=True)
    birth_other_mulgaon = models.CharField(max_length=200, blank=True, null=True)
    is_poverty_line = models.BooleanField(default=0,blank= True, null=True)
    upload_certificate_poverty_line = models.FileField(upload_to='poverty_line_certificates', blank=True, null=True)
    upload_parent_teacher_certificate = models.FileField(upload_to='parent_teacher_certificates', blank=True, null=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)



    class Meta:
        abstract = True


class StSchFormDetails(StudentApplicant):
    sch_session = models.ForeignKey(schSession, on_delete = models.CASCADE)
    student_category = models.ForeignKey(StudentCategory, on_delete = models.CASCADE,null=True, blank=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)


    def __str__(self):
        return self.email


class StLoanFormDetails(StudentApplicant):
    is_loan_received = models.BooleanField(default=0,blank= True, null=True)
    loan_amount = models.FloatField(blank=True, null=True)
    self_declaration_form = models.FileField(upload_to='declaration_form',blank=True, null=True)
    current_education_fee = models.CharField(max_length=200,blank=True,null=True)
    loan_amount_willing = models.CharField(max_length=200,blank=True,null=True)
    guarantor_certificate_one = models.FileField(upload_to='guarantor_certificate',blank=True, null=True)
    guarantor_name_one = models.CharField(max_length=100, blank=True, null=True)
    guarantor_address_one = models.CharField(max_length=500, blank=True, null=True)
    guarantor_mobile_one = PhoneNumberField(blank=True, null=True)
    guarantor_certificate_two = models.FileField(upload_to='guarantor_certificate',blank=True, null=True)
    guarantor_name_two = models.CharField(max_length=100, blank=True, null=True)
    guarantor_address_two = models.CharField(max_length=500, blank=True, null=True)
    guarantor_mobile_two = PhoneNumberField(blank=True, null=True)
    sch_session = models.ForeignKey(schSession, on_delete = models.CASCADE)
    student_category = models.ForeignKey(StudentCategory, on_delete = models.CASCADE, null=True,blank=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.email


class StudentApplicantDraft(Base):
    first_name = models.CharField(max_length=100, blank=True, null=True)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    first_name_marathi = models.CharField(max_length=100, blank=True, null=True)
    middle_name_marathi = models.CharField(max_length=100, blank=True, null=True)
    last_name_marathi = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    email = models.EmailField(max_length=50,blank=True, null=True)
    mobile = PhoneNumberField(blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    taluka = models.CharField(max_length=100, blank=True, null=True)
    mulgaon = models.CharField(max_length=100, blank=True, null=True)
    passed_college_name = models.CharField(max_length=500, blank=True, null=True)
    passed_education = models.CharField(max_length=100, blank=True, null=True)
    passed_education_percentage = models.FloatField(blank=True, null=True)
    passed_education_marksheet = models.FileField(upload_to='form_details',blank=True, null=True)
    current_education = models.CharField(max_length=100, blank=True, null=True)
    is_disablity_candidate =  models.BooleanField(default=0,blank=True, null=True)
    disablity_certificate = models.FileField(upload_to='student_applicant',blank=True, null=True)
    aadhar_card = models.FileField(upload_to='aadhar_files', blank=True, null=True)
    address_proof = models.FileField(upload_to='address_proofs', blank=True, null=True)
    income_certificate = models.FileField(upload_to='income_certificates', blank=True, null=True)
    bonafide_certificate = models.FileField(upload_to='bonafide_certificates', blank=True, null=True)
    ration_card = models.FileField(upload_to='ration_cards', blank=True, null=True)
    bank_name = models.CharField(max_length=200,null=True,blank=True)
    account_no = models.CharField(max_length=200,null=True,blank=True)
    account_holder = models.CharField(max_length=200,null=True,blank=True)
    branch_name = models.CharField(max_length=200,null=True,blank=True)
    ifsc_code = models.CharField(max_length=200,null=True,blank=True)
    is_birth_place_different = models.BooleanField(default=0,blank=True, null=True)
    birth_place = models.CharField(max_length=100,null=True,blank=True)
    is_certificate_sports =  models.BooleanField(default=0,blank=True, null=True)
    upload_certificate_sports = models.FileField(upload_to='sports_certificates', blank=True, null=True)
    is_alive =  models.BooleanField(default=0,blank=True, null=True)
    upload_certificate_isalive = models.FileField(upload_to='isalive_certificates', blank=True, null=True)
    is_district_level_player =  models.BooleanField(default=0,blank=True, null=True)
    upload_certificate_district_level = models.FileField(upload_to='district_level_certificates', blank=True, null=True)
    is_application_received_previously =  models.BooleanField(default=0,blank=True, null=True)
    college_distance = models.CharField(max_length=500,null=True,blank=True)
    college_travel_vehical = models.CharField(max_length=100,null=True,blank=True)
    college_expenditure_tohome = models.CharField(max_length=100,null=True,blank=True)
    family_details = models.CharField(max_length=1000,null=True,blank=True)
    family_income = models.CharField(max_length=1000,null=True,blank=True)
    tuition_fee = models.CharField(max_length=500,null=True,blank=True)
    cost_books = models.CharField(max_length=200,null=True,blank=True)
    cost_uniform = models.CharField(max_length=200,null=True,blank=True)
    academic_year_cost_travel = models.CharField(max_length=1000,null=True,blank=True)
    hostel_fees = models.CharField(max_length=300,null=True,blank=True)
    other_passed_Education = models.CharField(max_length=200, blank=True, null=True)
    other_current_education = models.CharField(max_length=200, blank=True, null=True)
    other_taluka = models.CharField(max_length=200, blank=True, null=True)
    other_district = models.CharField(max_length=200, blank=True, null=True)
    teacher_one = models.FileField(upload_to='teacher_one',blank=True, null=True)
    teacher_two = models.FileField(upload_to='teacher_two',blank=True, null=True)
    is_other_sch_received = models.BooleanField(default=0,blank= True, null=True)
    other_sch_received_amt = models.FloatField(blank=True, null=True)
    fee_receipt = models.FileField(upload_to='fee_receipt',blank=True, null=True)
    birth_other_taluka = models.CharField(max_length=200, blank=True, null=True)
    birth_other_district = models.CharField(max_length=200, blank=True, null=True)
    birth_other_mulgaon = models.CharField(max_length=200, blank=True, null=True)
    is_poverty_line = models.BooleanField(default=0,blank= True, null=True)
    upload_certificate_poverty_line = models.FileField(upload_to='poverty_line_certificates', blank=True, null=True)
    upload_parent_teacher_certificate = models.FileField(upload_to='parent_teacher_certificates', blank=True, null=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        abstract = True


class StSchFormDetailsDraft(StudentApplicantDraft):
        
    draft_status = models.BooleanField(default=False,blank=True, null=True)
    student_category = models.ForeignKey(StudentCategory, on_delete = models.CASCADE,null=True,blank=True)
    sch_session = models.ForeignKey(schSession, on_delete = models.CASCADE,null=True,blank=True)
    student_category = models.ForeignKey(StudentCategory, on_delete = models.CASCADE, blank=True, null=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.email


class StLoanFormDetailsDraft(StudentApplicantDraft):
    is_loan_received = models.BooleanField(default=0,blank=True, null=True)
    loan_amount = models.FloatField(blank=True, null=True)
    self_declaration_form = models.FileField(upload_to='declaration_form',blank=True, null=True)
    current_education_fee = models.CharField(max_length=200,blank=True,null=True)
    loan_amount_willing = models.CharField(max_length=200,blank=True,null=True)
    loan_draft_status = models.BooleanField(default=False,blank=True, null=True)
    guarantor_certificate_one = models.FileField(upload_to='guarantor_certificate',blank=True, null=True)
    guarantor_name_one = models.CharField(max_length=100, blank=True, null=True)
    guarantor_address_one = models.CharField(max_length=500, blank=True, null=True)
    guarantor_mobile_one = PhoneNumberField(blank=True, null=True)
    guarantor_certificate_two = models.FileField(upload_to='guarantor_certificate',blank=True, null=True)
    guarantor_name_two = models.CharField(max_length=100, blank=True, null=True)
    guarantor_address_two = models.CharField(max_length=500, blank=True, null=True)
    guarantor_mobile_two = PhoneNumberField(blank=True, null=True)
    sch_session = models.ForeignKey(schSession, on_delete = models.CASCADE,null=True,blank=True)
    student_category = models.ForeignKey(StudentCategory, on_delete = models.CASCADE, null=True, blank=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)


    def __str__(self):
        return self.email


        
class OrganizationApplicant(Base):
    name = models.CharField(max_length = 100, null = False ,blank=False)
    email = models.EmailField(max_length=50,blank=False, null=False)
    address = models.CharField(max_length = 500, null = True, blank=True)
    pincode = models.CharField(max_length=20,null=True, default=0 ,blank=True)
    authority_name = models.CharField(max_length = 100, null = True, blank=True)
    mobile = PhoneNumberField(null=False, blank=False)
    landline_no = PhoneNumberField(null=True, blank=True) 
    district = models.CharField(max_length=100, blank=True, null=True)
    taluka = models.CharField(max_length=100, blank=True, null=True)
    other_taluka = models.CharField(max_length=200, blank=True, null=True)
    other_district = models.CharField(max_length=200, blank=True, null=True)
    mulgaon = models.CharField(max_length=100, blank=True, null=True)
    organization_started = models.DateField(null=True, blank=True)
    is_org_register = models.BooleanField(default=0,blank= True, null=True)
    org_register_certificate = models.FileField(upload_to='org_register_certificate',blank=True, null=True)
    bank_name = models.CharField(max_length=200,null=True,blank=True)
    account_no = models.CharField(max_length=200,null=True,blank=True)
    account_holder = models.CharField(max_length=200,null=True,blank=True)
    branch_name = models.CharField(max_length=200,null=True,blank=True)
    ifsc_code = models.CharField(max_length=200,null=True,blank=True)
    is_scholarship_recevied = models.BooleanField(default=0,blank= True, null=True)
    cancelled_cheque = models.FileField(upload_to='cancelled_cheque',blank=True, null=True)
    student_book_count_first_year = models.CharField(max_length=500,null=True,blank=True)
    student_book_count_second_year = models.CharField(max_length=500,null=True,blank=True)
    student_book_count_third_year = models.CharField(max_length=500,null=True,blank=True)
    student_count_current_year = models.CharField(max_length=500,null=True,blank=True)
    expenditure_first_year = models.CharField(max_length=500,null=True,blank=True)
    expenditure_second_year = models.CharField(max_length=500,null=True,blank=True)
    expenditure_third_year = models.CharField(max_length=500,null=True,blank=True)
    details_source_income = models.CharField(max_length=500,null=True,blank=True)
    current_total_expenditure = models.FloatField(blank=True, null=True)
    bank_statement_first_year = models.FileField(upload_to='bank_statement_first_year',blank=True, null=True)
    bank_statement_second_year = models.FileField(upload_to='bank_statement_second_year',blank=True, null=True)
    bank_statement_third_year = models.FileField(upload_to='bank_statement_third_year',blank=True, null=True)
    item_details_expense = models.CharField(max_length=500,null=True,blank=True)
    employee_details = models.CharField(max_length=500,null=True,blank=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)


    class Meta:
        abstract = True



class OrganizationApplicantDraft(Base):
    name = models.CharField(max_length = 100, null = True ,blank=True)
    email = models.EmailField(max_length=50,blank=True, null=True)
    address = models.CharField(max_length = 500, null = True, blank=True)
    pincode = models.CharField(max_length=20,null=True, default=0 ,blank=True)
    authority_name = models.CharField(max_length = 100, null = True, blank=True)
    mobile = PhoneNumberField(null=True, blank=True)
    landline_no = PhoneNumberField(null=True, blank=True) 
    district = models.CharField(max_length=100, blank=True, null=True)
    taluka = models.CharField(max_length=100, blank=True, null=True)
    other_taluka = models.CharField(max_length=200, blank=True, null=True)
    other_district = models.CharField(max_length=200, blank=True, null=True)
    mulgaon = models.CharField(max_length=100, blank=True, null=True)
    organization_started = models.DateField(null=True, blank=True)
    is_org_register = models.BooleanField(default=0,blank=True, null=True)
    org_register_certificate = models.FileField(upload_to='org_register_certificate',blank=True, null=True)
    bank_name = models.CharField(max_length=200,null=True,blank=True)
    account_no = models.CharField(max_length=200,null=True,blank=True)
    account_holder = models.CharField(max_length=200,null=True,blank=True)
    branch_name = models.CharField(max_length=200,null=True,blank=True)
    ifsc_code = models.CharField(max_length=200,null=True,blank=True)
    is_scholarship_recevied = models.BooleanField(default=0,blank=True, null=True)
    cancelled_cheque = models.FileField(upload_to='cancelled_cheque',blank=True, null=True)
    student_book_count_first_year = models.CharField(max_length=500,null=True,blank=True)
    student_book_count_second_year = models.CharField(max_length=500,null=True,blank=True)
    student_book_count_third_year = models.CharField(max_length=500,null=True,blank=True)
    student_count_current_year = models.CharField(max_length=500,null=True,blank=True)
    expenditure_first_year = models.CharField(max_length=500,null=True,blank=True)
    expenditure_second_year = models.CharField(max_length=500,null=True,blank=True)
    expenditure_third_year = models.CharField(max_length=500,null=True,blank=True)
    details_source_income = models.CharField(max_length=500,null=True,blank=True)
    current_total_expenditure = models.FloatField(blank=True, null=True)
    bank_statement_first_year = models.FileField(upload_to='bank_statement_first_year',blank=True, null=True)
    bank_statement_second_year = models.FileField(upload_to='bank_statement_second_year',blank=True, null=True)
    bank_statement_third_year = models.FileField(upload_to='bank_statement_third_year',blank=True, null=True)
    item_details_expense = models.CharField(max_length=500,null=True,blank=True)
    employee_details = models.CharField(max_length=500,null=True,blank=True)
    draft_status = models.BooleanField(default= True,null=True,blank=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)


    class Meta:
        abstract = True


class VachnalayaForm(OrganizationApplicant):
    sch_session = models.ForeignKey(schSession, on_delete = models.CASCADE)
    vachanalay_form_status = models.BooleanField(default= False,null=True,blank=True)
    student_category = models.ForeignKey(StudentCategory, on_delete = models.CASCADE, null=True,blank=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.email


class SchoolForm(OrganizationApplicant):
    sch_session = models.ForeignKey(schSession, on_delete = models.CASCADE)
    name_of_principal = models.CharField(max_length=50,blank=True,null=True)
    school_form_status = models.BooleanField(default= False,null=True,blank=True)
    student_category = models.ForeignKey(StudentCategory, on_delete = models.CASCADE, null=True,blank=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)


    def __str__(self):
        return self.email


class AnganwadiForm(OrganizationApplicant):
    sch_session = models.ForeignKey(schSession, on_delete = models.CASCADE)
    group_photo = models.FileField(upload_to="group_photo",blank=True, null=True)
    anganwadi_form_status = models.BooleanField(default= False,null=True,blank=True)
    hostel_type = models.CharField(max_length=50,blank=True, null=True)
    student_category = models.ForeignKey(StudentCategory, on_delete = models.CASCADE, null=True,blank=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


class VachnalayaFormDraft(OrganizationApplicantDraft):
    sch_session = models.ForeignKey(schSession, on_delete = models.CASCADE)
    vachanalay_form_status = models.BooleanField(default= True,null=True,blank=True)
    student_category = models.ForeignKey(StudentCategory, on_delete = models.CASCADE, null=True,blank=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.email


class SchoolFormDraft(OrganizationApplicantDraft):
    sch_session = models.ForeignKey(schSession, on_delete = models.CASCADE)
    name_of_principal = models.CharField(max_length=50,blank=True,null=True)
    school_form_status = models.BooleanField(default= True,null=True,blank=True)
    student_category = models.ForeignKey(StudentCategory, on_delete = models.CASCADE, null=True,blank=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.email


class AnganwadiFormDraft(OrganizationApplicantDraft):
    sch_session = models.ForeignKey(schSession, on_delete = models.CASCADE)
    group_photo = models.FileField(upload_to="group_photo",blank=True, null=True)
    anganwadi_form_status = models.BooleanField(default= True,null=True,blank=True)
    hostel_type = models.CharField(max_length=50,blank=True, null=True)
    student_category = models.ForeignKey(StudentCategory, on_delete = models.CASCADE, null=True,blank=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)


    def __str__(self):

        return self.email



class InstitutionForm(OrganizationApplicant):
    sch_session = models.ForeignKey(schSession, on_delete = models.CASCADE)
    group_photo = models.FileField(upload_to="group_photo",blank=True, null=True)
    institution_form_status = models.BooleanField(default= False,null=True,blank=True)
    hostel_type = models.CharField(max_length=50,blank=True, null=True)
    student_category = models.ForeignKey(StudentCategory, on_delete = models.CASCADE, null=True,blank=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.email


class InstitutionFormDraft(OrganizationApplicantDraft):
    sch_session = models.ForeignKey(schSession, on_delete = models.CASCADE)
    group_photo = models.FileField(upload_to="group_photo",blank=True, null=True)
    institution_form_status = models.BooleanField(default= True,null=True,blank=True)
    hostel_type = models.CharField(max_length=50,blank=True, null=True)
    student_category = models.ForeignKey(StudentCategory, on_delete = models.CASCADE, null=True,blank=True)
    text_field_1 = models.CharField(max_length=100, blank=True, null=True)
    text_field_2 = models.CharField(max_length=100, blank=True, null=True)
    text_field_3 = models.CharField(max_length=100, blank=True, null=True)


    def __str__(self):
        return self.email


class ReportFilters(Base):
    display_name = models.CharField(max_length=100)
    db_name = models.CharField(max_length=100)
    query_string = models.CharField(max_length=500,null=True,blank=True)
    replacable_variable = models.CharField(max_length=100, null=True,blank=True)
    is_id = models.IntegerField(default=0)

    def __str__(self):
        return self.display_name


class ReportManagement(Base):
    name = models.CharField(max_length=500)
    description = models.CharField(max_length=500, null=True, blank=True)
    query = models.TextField(max_length=10000)
    report_type = models.CharField(default="Query", max_length=25)
    user = models.ManyToManyField(User, blank=True)
    columns_to_skip = models.IntegerField(default=0)
    filters_list = models.ManyToManyField(ReportFilters, blank=True)


    def __str__(self):
        return self.name