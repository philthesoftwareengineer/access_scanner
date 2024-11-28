import requests
import json
from wcag_zoo.validators.anteater import Anteater
from wcag_zoo.validators.ayeaye import Ayeaye
from wcag_zoo.validators.glowworm import Glowworm
from wcag_zoo.validators.molerat import Molerat
from wcag_zoo.validators.tarsier import Tarsier
from .utils import save_accessibility_result
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


def check_accessibility(response):
    html_content = response.text
    url = response.url
    datetime_stamp = datetime.now().isoformat()

    # Categorize results
    all_results = {
        'success': [],
        'failures': [],
        'warnings': [],
        'skipped': []
    }

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
                        
    save_accessibility_result(all_results, url)
    
    return all_results if any(all_results.values()) else {"message": "No accessibility issues found."}



    # else:
    #     return ["Issue with response content."]


if __name__ == "__main__":
    url = "http://127.0.0.1:8000/"
    
    response = requests.get(url)
    recommendations = check_accessibility(response)

    for rec in recommendations:
        print(rec)
