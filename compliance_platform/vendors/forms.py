from django import forms

from .models import Vendor


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['name', 'services', 'tech_stack', 'risk_score', 'contact_email', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'services': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tech_stack': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'risk_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
