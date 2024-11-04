import requests
import json
from wcag_zoo.validators.anteater import Anteater
from wcag_zoo.validators.ayeaye import Ayeaye
from wcag_zoo.validators.glowworm import Glowworm
from wcag_zoo.validators.molerat import Molerat
from wcag_zoo.validators.tarsier import Tarsier
from .utils import save_accessibility_result

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
    """
    Check the accessibility of a webpage using WCAG-zoo validators
    
    Args:
        response: The response from a GET request

    Returns:
        list: A list of recommendations to improve accessibility
    """
    # Below if statement used when script was independant of web app
    # if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
        # html_content = response.text

    html_content = response.text
    recommendations = []
    url = response.url

    # WCAG Validators
    validators = [Anteater, Ayeaye, Glowworm, Molerat, Tarsier]

    for ValidatorClass in validators:
        result = run_validator(ValidatorClass, html_content)
        with open('data.json', 'a') as file:
            json.dump(result, file, indent=4)

        failures = result.get('failures', [])
        warnings = result.get('warnings', [])
        skipped = result.get('skipped', [])

        if failures or warnings:
            validator_name = ValidatorClass.__name__
            recommendations.append(f"--- {validator_name} ---")

            if failures:
                recommendations.append(f"Failures ({len(failures)}):")
                for guideline, techniques in failures.items():
                    for technique, items in techniques.items():
                        for failure in items:
                            recommendations.append(f"  - {failure.get('message', 'No message available')}")
                            save_accessibility_result(url, 'Failed', failure.get('message', 'No message available'))

            if warnings:
                recommendations.append(f"Warnings ({len(warnings)}):")
                for guideline, techniques in warnings.items():
                    for technique, items in techniques.items():
                        for warning in items:
                            recommendations.append(f"  - {warning.get('message', 'No message available')}")
                            save_accessibility_result(url, 'Warning', warning.get('message', 'No message available'))

            if skipped:
                recommendations.append(f"Skipped elements ({len(skipped)}):")
                for skip in skipped:
                    if isinstance(skip, dict) and 'message' in skip:
                        recommendations.append(f"  - {skip['message']}")
                        save_accessibility_result(url, 'Skipped', skip.get('message', 'No message available'))
                    else:
                        recommendations.append(f"  - {skip}")
    
    return recommendations if recommendations else ["No accessibility issues found."]
    # else:
    #     return ["Issue with response content."]


if __name__ == "__main__":
    url = "http://127.0.0.1:8000/"
    
    response = requests.get(url)
    recommendations = check_accessibility(response)

    for rec in recommendations:
        print(rec)
