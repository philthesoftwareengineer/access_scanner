from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from .models import AccessibilityResult
import json
import requests

class ViewsTestCase(TestCase):
    
    def setUp(self):
        self.client = Client()

    @patch('scanner.views.requests.get')
    @patch('scanner.views.run_access_scan')
    @patch('scanner.views.save_accessibility_result')
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
                "skipped": [{"section_type": "skipped", "message": "Example skipped"}]
            })
        )

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'scanner/dashboard.html')
        self.assertEqual(response.context['failure_count'], 1)
        self.assertEqual(response.context['warning_count'], 0)
        self.assertEqual(response.context['skipped_count'], 0)
        self.assertEqual(response.context['success_count'], 0)
        self.assertEqual(response.context['failure_example'], "Example failure")
        self.assertEqual(response.context['warning_example'], "No warnings recorded")
        self.assertEqual(response.context['skipped_example'], "No skipped elements recorded")

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


