from django.shortcuts import render
import requests
from .forms import UrlForm
from .wcag_checker import run_access_scan
from .models import AccessibilityResult

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
            except requests.exceptions.RequestException as err:
                results = {'error': f"Could not fetch teh URL. Error: {err}"}
    else:
        form = UrlForm()

    return render(request, 'scanner/check_url.html', {'form': form, 'results': results})


def dashboard(request):
    # Get the most recent URL check
    recent_result = AccessibilityResult.objects.order_by('-timestamp').first()

    if recent_result:
        # Extract counts for warnings, failures, and skipped elements
        warnings_count = AccessibilityResult.objects.filter(
            url=recent_result.url, status='Warning'
        ).count()

        failures_count = AccessibilityResult.objects.filter(
            url=recent_result.url, status='Failed'
        ).count()

        skipped_count = AccessibilityResult.objects.filter(
            url=recent_result.url, status='Skipped'
        ).count()

        # Get one example message for each type
        warning_example = AccessibilityResult.objects.filter(
            url=recent_result.url, status='Warning'
        ).values_list('message', flat=True).first()

        failure_example = AccessibilityResult.objects.filter(
            url=recent_result.url, status='Failed'
        ).values_list('message', flat=True).first()

        skipped_example = AccessibilityResult.objects.filter(
            url=recent_result.url, status='Skipped'
        ).values_list('message', flat=True).first()
    else:
        warnings_count = 0
        failures_count = 0
        skipped_count = 0
        warning_example = "No warnings recorded"
        failure_example = "No failures recorded"
        skipped_example = "No skipped elements recorded"

    context = {
        'url': recent_result.url if recent_result else 'No URL checked yet',
        'warning_count': warnings_count,
        'failure_count': failures_count,
        'skipped_count': skipped_count,
        'warning_example': warning_example,
        'failure_example': failure_example,
        'skipped_example': skipped_example,
    }

    return render(request, 'scanner/dashboard.html', context)
