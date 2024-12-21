from django import forms
from .models import HudumaCentre

class HudumaCentreForm(forms.Form):
    # This will render a select field with choices dynamically fetched from the database
    centre = forms.ModelChoiceField(
        queryset=HudumaCentre.objects.all(),
        empty_label="Select Centre",  # Optional, for placeholder text
        widget=forms.Select(attrs={'class': 'form-select'})
    )