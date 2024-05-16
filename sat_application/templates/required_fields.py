import requests
from bs4 import BeautifulSoup

def get_required_fields(form):
    required_fields = []
    for input_tag in form.find_all('input', {'required': True}):
        if input_tag.get('name'):
            required_fields.append(input_tag.get('name'))
    return required_fields

def get_non_required_fields(form):
    non_required_fields = []
    for input_tag in form.find_all('input', {'required': False}):
        if input_tag.get('name'):
            non_required_fields.append(input_tag.get('name'))
    return non_required_fields

SOURCE_HTML = "LOCAL"
#Options - URL or LOCAL.
#QA Team uses URL
#Dev Team uses LOCAL.
#Switch the above Variable to the correct one

# URL of the HTML page
if(SOURCE_HTML == "URL"):
    url = 'https://example.com/form.html'

    # # Send a GET request to the URL
    contents = requests.get(url)
elif(SOURCE_HTML == "LOCAL"):
    with open('create_loan_scholarship_details_form.html', 'r', encoding='utf-8') as f:
        contents = f.read()
# Parse the HTML content

soup = BeautifulSoup(contents, 'html.parser')

# Find the form on the page
form = soup.find('form')

if form:
    # Get the required fields
    required_fields = get_required_fields(form)
    print('Required fields:', required_fields)

    # Get the non-required fields
    non_required_fields = get_non_required_fields(form)
    print('Non-required fields:', non_required_fields)
else:
    print('No form found on the page.')
