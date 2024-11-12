from django.shortcuts import render
import requests
from .forms import UrlForm
from .wcag_checker import run_access_scan
from .models import AccessibilityResult
from .utils import save_accessibility_result
from django.http import JsonResponse, HttpResponse, FileResponse
import pandas as pd
import json
import tempfile
import os

def check_url(request):
    results = None
    if request.method == 'POST':
        form = UrlForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            # Send GET request and run scanning script
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    results = run_access_scan(response)
                    save_accessibility_result(results, url)
            except requests.exceptions.RequestException as err:
                results = {'error': f"Could not fetch teh URL. Error: {err}"}
    else:
        form = UrlForm()

    return render(request, 'scanner/check_url.html', {'form': form, 'results': results})


def dashboard(request):
   # Retrieve the most recent result
    recent_result = AccessibilityResult.objects.order_by('-timestamp').first()

    if recent_result:
        json_data = json.loads(recent_result.json_response)

        # Flatten all entries in 'failures' into a single list, regardless of section_type
        entries = json_data.get("failures", [])

        # Normalize the JSON data while ignoring the outer keys
        df = pd.json_normalize(entries, sep='_')

        failures_df = df[df['section_type'] == 'failures']
        warnings_df = df[df['section_type'] == 'warnings']
        success_df = df[df['section_type'] == 'success']
        skipped_df = df[df['section_type'] == 'skipped']

        failures_count = len(failures_df)
        warnings_count = len(warnings_df)
        success_count = len(success_df)
        skipped_count = len(skipped_df)

        failure_example = failures_df['message'].iloc[0] if failures_count > 0 else 'No failures recorded'
        warning_example = warnings_df['message'].iloc[0] if warnings_count > 0 else 'No warnings recorded'
        skipped_example = skipped_df['message'].iloc[0] if skipped_count > 0 else 'No skipped elements recorded'

    else:
        failures_count = warnings_count = skipped_count = success_count = 0
        failure_example = "No failures recorded"
        warning_example = "No warnings recorded"
        skipped_example = "No skipped elements recorded"

    context = {
        'url': recent_result.url if recent_result else 'No URL checked yet',
        'failure_count': failures_count,
        'warning_count': warnings_count,
        'skipped_count': skipped_count,
        'success_count': success_count,
        'failure_example': failure_example,
        'warning_example': warning_example,
        'skipped_example': skipped_example,
    }

    return render(request, 'scanner/dashboard.html', context)

def download_json(request):
    recent_result = AccessibilityResult.objects.order_by('-timestamp').first()

    if recent_result:
        json_data = json.loads(recent_result.json_response)

        #formatted_json = json.dumps(json_data, indent=4)
        response = HttpResponse(json.dumps(json_data, indent=4), content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="accessibility_results.json"'

        return response
    else:
        return JsonResponse({'error': 'No results found to download'}, status=404)