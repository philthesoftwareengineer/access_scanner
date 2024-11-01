# scanner/utils.py

from .models import AccessibilityResult

def save_accessibility_result(url, status, message):
    """
    Save a scan result to the database
    
    Args:
        url (str): The URL that was checked
        status (str): Status of the result 
        message (str): The message describing the issue found
    """
    AccessibilityResult.objects.create(url=url, status=status, message=message)
