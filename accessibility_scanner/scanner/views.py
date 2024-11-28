from django.shortcuts import render, redirect
import requests
from .forms import UrlForm, LoginForm, RegisterForm
from .wcag_checker import run_access_scan
from .models import AccessibilityResult
from .utils import save_accessibility_result
from django.http import JsonResponse, HttpResponse, FileResponse
import pandas as pd
import json
import tempfile
import os
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages



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
                else:
                    results = {'error': f"Error with request: {str(response.status_code)}"}
                    save_accessibility_result(results, url)
            except requests.exceptions.RequestException as err:
                results = {'error': f"Could not fetch the URL. Error: {err}"}
    else:
        form = UrlForm()

    return render(request, 'scanner/check_url.html', {'form': form, 'results': results})


def dashboard(request):
   # Retrieve the most recent result
    recent_result = AccessibilityResult.objects.order_by('-timestamp').first()

    if recent_result:
        json_data = json.loads(recent_result.json_response)

        # # Flatten all entries in 'failures' into a single list, regardless of section_type

        # entries = json_data.get("failures", [])


        # Normalize the JSON data while ignoring the outer keys
        # df = pd.json_normalize(json_data, sep='_')
        # try:
        #     failures_df = df[df['section_type'] == 'failures']
        # except KeyError:
        #     print("Caught the keyerror\n")
        #     context = {
        #         'url': recent_result.url if recent_result else 'No URL checked',
        #         'failure_count': 0,
        #         'warning_count': 0,
        #         'skipped_count': 0,
        #         'success_count': 0,
        #         'failure_example': "N/A",
        #         'warning_example': "N/A",
        #         'skipped_example': "N/A",
        #     }
        #     return render(request, 'scanner/dashboard.html', context)  
        failures_df = pd.DataFrame(json_data['failures'])
        warnings_df = pd.DataFrame(json_data['warnings'])
        success_df = pd.DataFrame(json_data['success'])
        skipped_df = pd.DataFrame(json_data['skipped'])      
        # warnings_df = df[df['section_type'] == 'warnings']
        # success_df = df[df['section_type'] == 'success']
        # skipped_df = df[df['section_type'] == 'skipped']

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
    
def sign_in(request):
    """
    Handles both GET and POST requests for user login

    Args:
        request (HttpRequest): The HTTP request object

    Returns:
        HttpResponse: The rendered login page or a redirection to the log page on successful login
    """
    if request.method == 'GET':
        if request.user.is_authenticated:
            return redirect('log')

        form = LoginForm()
        return render(request, 'scanner/login.html', {'form': form})
    
    elif request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f"Hello {username.title()}, let's get logging!")
                return redirect('check_url')
            
        # form isn't valid or the user's unauthenticated
        messages.error(request, f"Invalid username or password, please try again!")
        return render(request, 'scanner/login.html', {'form': form})

   
def sign_out(request):
    """
    Logs the user out and displays a confirmation message

    Args:
        request (HttpRequest): The HTTP request object

    Returns:
        HttpResponse: A redirection to the login page after logout
    """
    logout(request)
    messages.success(request, f"You're now logged out. Why are you logging out?")
    return redirect('login')


def register(request):
    """
    Handles both GET and POST requests for user registration

    Args:
        request (HttpRequest): The HTTP request object

    Returns:
        HttpResponse: The rendered registration page or a redirection to the log page on successful registration
    """
    if request.method == 'GET':
        form = RegisterForm()
        return render(request, 'scanner/register.html', {'form': form})
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            messages.success(request, 'Registration successful. Welcome to the competition!')
            login(request, user)
            return redirect('login')
        else:
            return render(request, 'scanner/register.html', {'form': form})
