from bs4 import BeautifulSoup

def check_form_fields(html_file):
    total_form_tags = 0
    id_present = 0
    id_absent = 0
    with open(html_file, encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        
        form_fields = soup.find_all(['input', 'textarea', 'select', 'button'])
        
        total_form_tags = len(form_fields)
        for field in form_fields:
            if not field.has_attr('id'):
                id_absent += 1
            else:
                id_present += 1
    
    return total_form_tags, id_present, id_absent

# Provide the path to your HTML file here
file_path = input("Enter file path: ")

html_file_path = str(file_path)

validation = check_form_fields(html_file_path)
print("Total form tags: "+ str(validation[0]))
print("Total IDs present: "+ str(validation[1]))
print("Total IDs absent: "+ str(validation[2]))