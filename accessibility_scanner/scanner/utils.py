# scanner/utils.py
#import pandas as pd
#import sqlite3

#from .models import AccessibilityResult

from .models import AccessibilityResult
from django.utils import timezone
import json

def save_accessibility_result(results, url):

    """
    Save the accessibility results to the AccessibilityResult model using Django's ORM.
    """
    # Prepare the data as JSON
    json_results = json.dumps(results)

    # Create a new AccessibilityResult entry
    AccessibilityResult.objects.create(
        url=url,  # Extract URL from results if available
        json_response=json_results,
        timestamp=timezone.now()
    )
    