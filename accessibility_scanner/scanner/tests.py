from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from .models import AccessibilityResult
import json
import requests
import re
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from .wcag_script import run_validator, check_accessibility, check_for_serif_fonts
#from .utils import save_accessibility_result

#################################################
# views.py tests

class ViewsTestCase(TestCase):
    
    def setUp(self):
        self.client = Client()

    @patch('scanner.views.requests.get')
    @patch('scanner.views.run_access_scan')
    @patch('scanner.wcag_script.save_accessibility_result')
    def test_check_url_success(self, mock_save_result, mock_run_scan, mock_requests_get):
        '''
        Creates a mock successful request and then checks the functionality of checking the
        url
        '''
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests_get.return_value = mock_response

        mock_scan_result = {'result': 'scan_data'}
        mock_run_scan.return_value = mock_scan_result

        response = self.client.post(reverse('check_url'), {'url': 'http://example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'scanner/check_url.html')
        self.assertIn('results', response.context)
        self.assertEqual(response.context['results'], mock_scan_result)

    @patch('scanner.views.requests.get')
    def test_check_url_invalid_request(self, mock_requests_get):
        '''
        This test creates a mock failed request and then attempts to check the results
        '''
        mock_requests_get.side_effect = requests.exceptions.RequestException("Request failed")

        response = self.client.post(reverse('check_url'), {'url': 'http://example.com'})

        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertIn('error', response.context['results'])
        self.assertIn("Could not fetch the URL", response.context['results']['error'])

    def test_dashboard_no_results(self):
        '''
        This test checks the dashboard when there are no results from teh request
        '''
        response = self.client.get(reverse('dashboard'))


        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'scanner/dashboard.html')
        self.assertEqual(response.context['failure_count'], 0)
        self.assertEqual(response.context['warning_count'], 0)
        self.assertEqual(response.context['skipped_count'], 0)
        self.assertEqual(response.context['success_count'], 0)
        self.assertEqual(response.context['failure_example'], 'No failures recorded')
        self.assertEqual(response.context['serif_font_check'], "No result recorded")

    def test_dashboard_with_results(self):
        '''
        This test creates a mock entry int eh database and then tests the dashboard view
        with these results
        '''
        AccessibilityResult.objects.create(
            url="http://example.com",
            json_response=json.dumps({
                "failures": [{"section_type": "failures", "message": "Example failure"}],
                "warnings": [{"section_type": "warnings", "message": "Example warning"}],
                "success": [{"section_type": "success", "message": "Example success"}],
                "skipped": [{"section_type": "skipped", "message": "Example skipped"}],
                "serif_font_check": ["No serif fonts found in url."]
            })
        )

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'scanner/dashboard.html')
        self.assertEqual(response.context['failure_count'], 1)
        self.assertEqual(response.context['warning_count'], 1)
        self.assertEqual(response.context['skipped_count'], 1)
        self.assertEqual(response.context['success_count'], 1)
        self.assertEqual(response.context['failure_example'], "Example failure")
        self.assertEqual(response.context['warning_example'], "Example warning")
        self.assertEqual(response.context['skipped_example'], "Example skipped")
        self.assertEqual(response.context['serif_font_check'], "No serif fonts found in url.")

    def test_download_json_no_results(self):
        '''
        This test checks that attempting to download a json file with no results creates
        an error
        '''
        response = self.client.get(reverse('download_json'))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'error': 'No results found to download'})

    def test_download_json_with_results(self):
        '''
        Creates mock results in the database and then tests the functionality of downloading
        the json file
        '''
        AccessibilityResult.objects.create(
            url="http://example.com",
            json_response=json.dumps({
                "failures": [{"section_type": "failures", "message": "Example failure"}]
            })
        )

        response = self.client.get(reverse('download_json'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="accessibility_results.json"')
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn("Example failure", response.content.decode('utf-8'))

###############################
# wcag_script.py tests

class AccessibilityTests(unittest.TestCase):

    @patch('scanner.wcag_script.Anteater')
    def test_run_validator_success(self, MockAnteater):
        '''
        Testing Anteater validator
        '''
        mock_validator_instance = MockAnteater.return_value
        mock_validator_instance.validate_document.return_value = {
            'failures': {
                'guideline1': {
                    'technique1': [
                        {'message': 'Example failure', 'error_code': 'E1'}
                    ]
                }
            }
        }

        html_content = "<html><body>Test</body></html>"
        result = run_validator(MockAnteater, html_content)

        self.assertIn('failures', result)
        self.assertEqual(result['failures']['guideline1']['technique1'][0]['message'], 'Example failure')
        mock_validator_instance.validate_document.assert_called_once()

    @patch('scanner.wcag_script.requests.get')
    @patch('scanner.wcag_script.save_accessibility_result')
    @patch('scanner.wcag_script.run_validator')
    def test_check_accessibility_with_issues(self, mock_run_validator, mock_save_accessibility_result, mock_requests_get):
        '''
        Creating a bad validator response and checking the function returns the expected result
        '''
        mock_response = MagicMock()
        mock_response.text = "<html><body>Example content</body></html>"
        mock_response.url = "http://example.com"

        mock_requests_get.return_value = mock_response

        mock_run_validator.return_value = {
            'failures': {
                'guideline1': {
                    'technique1': [
                        {'message': 'Failure message', 'error_code': 'F1', 'xpath': '//div'}
                    ]
                }
            },
            'warnings': {},
            'skipped': {}
        }

        result = check_accessibility(mock_response)
        #print(json.dumps(result, indent=2))


        self.assertIn('failures', result)
        self.assertEqual(len(result['failures']), 5)
        self.assertEqual(result['failures'][0]['message'], 'Failure message')


        mock_save_accessibility_result.assert_called_once_with(result, "http://example.com")

    @patch('scanner.wcag_script.save_accessibility_result')
    def test_check_accessibility_no_issues(self, mock_save_accessibility_result):
        """
        Test the accessibility check when no issues are found in the response.
        """
        # Create a mock response with valid HTML content and a URL
        mock_response = MagicMock()
        mock_response.text = "<html><body>No issues here</body></html>"
        mock_response.url = "http://example.com"

        # Mock run_validator to return empty results for all validators
        with patch('scanner.wcag_script.run_validator') as mock_run_validator:
            mock_run_validator.return_value = {
                'success': {},
                'failures': {},
                'warnings': {},
                'skipped': {}
            }

            # Call the function under test
            result = check_accessibility(mock_response)

            # Define the expected result, including the serif_font_check key
            expected_result = {
                'success': [],
                'failures': [],
                'warnings': [],
                'skipped': [],
                'serif_font_check': ['No serif fonts found in url.']
            }

            # Assertions
            self.assertEqual(result, expected_result)
            mock_save_accessibility_result.assert_called_once_with(expected_result, "http://example.com")




    def test_run_validator_empty_html(self):
        '''
        Testing an empty html response
        '''
        html_content = ""
        with patch('scanner.wcag_script.Ayeaye') as MockAyeaye:
            mock_validator_instance = MockAyeaye.return_value
            mock_validator_instance.validate_document.return_value = {}

            result = run_validator(MockAyeaye, html_content)


            self.assertEqual(result, {})
            mock_validator_instance.validate_document.assert_called_once_with(b"")

    @patch('scanner.wcag_script.run_validator')
    def test_check_accessibility_handles_wrong_format_results(self, mock_run_validator):
        '''
        Testing a wrong-format response
        '''
        mock_response = MagicMock()
        mock_response.text = "<html><body>wrong format results</body></html>"
        mock_response.url = "http://example.com"

        mock_run_validator.return_value = {'failures': "This is not a dictionary"}

        with self.assertRaises(AttributeError):
            check_accessibility(mock_response)


class CheckForSerifFontsTests(unittest.TestCase):

    def test_check_for_serif_fonts_with_serif(self):
        '''
        Tests the function when serif fonts are present in the content.
        '''
        content = """
        <html>
            <style>
                body { font-family: "Times New Roman", serif; }
                p { font-family: Georgia, serif; }
            </style>
        </html>
        """
        result = check_for_serif_fonts(content)
        self.assertEqual(result, "Serif font found in url.")

    def test_check_for_serif_fonts_without_serif(self):
        '''
        Tests the function when no serif fonts are present in the content.
        '''
        content = """
        <html>
            <style>
                body { font-family: Arial, sans-serif; }
                p { font-family: Helvetica, sans-serif; }
            </style>
        </html>
        """
        result = check_for_serif_fonts(content)
        self.assertEqual(result, "No serif fonts found in url.")

    def test_check_for_serif_fonts_mixed_fonts(self):
        '''
        Tests the function when both serif and sans-serif fonts are present in the content.
        '''
        content = """
        <html>
            <style>
                body { font-family: "Times New Roman", serif; }
                p { font-family: Arial, sans-serif; }
            </style>
        </html>
        """
        result = check_for_serif_fonts(content)
        self.assertEqual(result, "Serif font found in url.")

    def test_check_for_serif_fonts_empty_content(self):
        '''
        Tests the function with empty content.
        '''
        content = ""
        result = check_for_serif_fonts(content)
        self.assertEqual(result, "No serif fonts found in url.")
