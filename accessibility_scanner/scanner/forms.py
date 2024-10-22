from django import forms

class UrlForm(forms.Form):
    url = forms.URLField(label='Enter the URLto check', max_length=200)