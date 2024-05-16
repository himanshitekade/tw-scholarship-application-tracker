from .models import *
from django.apps import apps

import pytz
from datetime import date, datetime
import decimal
# from tw_sat.settings import TIME_ZONE
# from django.utils import timezone


import mysql.connector
from decouple import config

# connecting mysql database
connection = mysql.connector.connect(
  host=config('DATABASE_HOST'),
  user=config('DATABASE_USER'),
  password=config('DATABASE_PASSWORD'),
  database=config('DATABASE_NAME')
)

def naiveTimeConversion(date):
    aware_tz = pytz.timezone(TIME_ZONE)                     
    aware_time = aware_tz.localize(date)
    return aware_time

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        obj = str(obj)
        return obj

    if isinstance(obj, decimal.Decimal):
        return float(obj)

    raise TypeError ("Type %s not serializable" % type(obj))


import calendar
from datetime import date,datetime, timedelta

def get_days_in_month(month,year):

    _, days_in_month = calendar.monthrange(year, month)
    start_date = date(year,month,1)
    end_date = date(year,month,days_in_month)

    return start_date, end_date

# Monday to Sunday
def get_last_week_dates():
    today = datetime.today()
    last_week_start = today - timedelta(days=today.weekday() + 7)
    last_week_end = last_week_start + timedelta(days=6)
    return last_week_start, last_week_end


def get_last_month_and_year():
    today = datetime.today()
    last_month = today.month - 1 if today.month > 1 else 12
    last_year = today.year if today.month > 1 else today.year - 1
    return last_month, last_year


def get_last_four_months_days(total_months):
    today = datetime.today()
    last_four_months_days = []
    

    for i in range(total_months):
        month = today.month - i-1
        year = today.year

        if month <= 0:
            month += 12
            year -= 1

        _, days_in_month = calendar.monthrange(year, month)

        last_four_months_days.append(days_in_month)
        total_days = sum(last_four_months_days)
    return total_days

def get_total_days_in_year(year):
    return 365 if not calendar.isleap(year) else 366


import json
from tw_sat.settings import BASE_DIR
import os

def generate_and_save_json(data, creator):
    # Fetch data from the Django model or create a dictionary manually
    json_data = {
        "action": "csv",
        "data": data,
        "createdBy": creator
    }

    # Convert data to JSON string
    json_data = json.dumps(json_data,default=json_serial)

    # Open a file in write mode

    path = os.path.join(BASE_DIR,"sat_application/report_json.json")

    print(path)
    with open(path, "w+") as file:
        # Write the JSON string to the file
        file.write(json_data)
        file.close()
    
    return path
    # Call the function to generate and save the JSON
