from django.shortcuts import render
import requests
from .forms import UrlForm
from .wcag_checker import run_access_scan

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


# Create your views here.
