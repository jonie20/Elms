from django import forms
from .models import HudumaCentre, Account
from django.contrib.auth.models import Group
class HudumaCentreForm(forms.Form):
    # This will render a select field with choices dynamically fetched from the database
    centre = forms.ModelChoiceField(
        queryset=HudumaCentre.objects.all(),
        empty_label="Select Centre",  # Optional, for placeholder text
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']

class AssignGroupForm(forms.Form):
    user = forms.ModelChoiceField(queryset= Account.objects.all(), label="Select User")
    group = forms.ModelChoiceField(queryset=Group.objects.all(), label="Select Group")