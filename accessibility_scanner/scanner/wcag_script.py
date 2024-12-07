import requests
import json
import re
from wcag_zoo.validators.anteater import Anteater
from wcag_zoo.validators.ayeaye import Ayeaye
from wcag_zoo.validators.glowworm import Glowworm
from wcag_zoo.validators.molerat import Molerat
from wcag_zoo.validators.tarsier import Tarsier
#from .utils import save_accessibility_result
from datetime import datetime

def run_validator(ValidatorClass, html_content):
    """
    Runs a validator on the HTML content

    Args:
        ValidatorClass (class): The WCAG validator to use
        html_content (str): The HTML content of the webpage

    Returns:
        dict: The validation results; (success, failures, warnings, skipped elements)
    """
    
    validator = ValidatorClass()
    
    # HTML content has to be turned into bytes for the validator to work
    html_content_bytes = html_content.encode('utf-8')
    result = validator.validate_document(html_content_bytes)
    return result

def check_for_serif_fonts(content):
    # with open(file_path, 'r', encoding='utf-8') as file:
    #     content = file.read()
    
    serif_font_pattern = r"font-family:.*?\b([^;]*\bserif\b[^;]*)(?!sans-serif)"
    matches = re.findall(serif_font_pattern, content, re.IGNORECASE)
    
    serif_fonts = [match.strip() for match in matches if 'sans-serif' not in match.lower()]
    
    if serif_fonts:
        return "Serif font found in url."
        # for font in serif_fonts:
        #     print(f"- {font}\n")
    else:
        return "No serif fonts found in url."


def check_accessibility(response):
    html_content = response.text
    # commented out lines below for testing example htmls
    # with open('bad_example.html', 'r', encoding='utf-8') as file:
    #     html_content = file.read()
    url = response.url
    datetime_stamp = datetime.now().isoformat()

    # Categorize results
    all_results = {
        'success': [],
        'failures': [],
        'warnings': [],
        'skipped': [], 
        'serif_font_check': [],
    }

    all_results['serif_font_check'].append(check_for_serif_fonts(html_content))

    # WCAG Validators
    validators = [Anteater, Ayeaye, Glowworm, Molerat, Tarsier]

    for ValidatorClass in validators:
        result = run_validator(ValidatorClass, html_content)
        
        for section, content in result.items():
            for guideline, items in content.items():
                for technique, entries in items.items():
                    for entry in entries:
                        # Define the type of issue, e.g., based on some condition in `entry`
                        issue_type = section  # Default to 'failures' if no type provided
                        
                        row = {
                            'datetime': datetime_stamp,
                            'url': url,
                            'section_type': section,
                            'guideline': entry.get('guideline'),
                            'technique': entry.get('technique'),
                            'message': entry.get('message'),
                            'error_code': entry.get('error_code'),
                            'xpath': entry.get('xpath'),
                            'classes': entry.get('classes'),
                            'id': entry.get('id')
                        }
                        
                        # Append to appropriate category
                        all_results[issue_type].append(row)
    with open("sample.json", "w") as file:
        json.dump(all_results, file)
                        
    #save_accessibility_result(all_results, url)
    
    return all_results if any(all_results.values()) else {"message": "No accessibility issues found."}



    # else:
    #     return ["Issue with response content."]


if __name__ == "__main__":
    url = "https://www.bbc.com"
    
    response = requests.get(url)
    recommendations = check_accessibility(response)

    # for rec in recommendations:
    #     print(rec)
    print(recommendations)
