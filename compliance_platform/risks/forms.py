from django import forms

from .models import Risk


class RiskForm(forms.ModelForm):
    class Meta:
        model = Risk
        fields = [
            'title', 'description', 'severity', 'linked_control',
            'linked_cve', 'linked_vendor', 'mitigation_status',
            'mitigation_plan', 'assigned_to',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'severity': forms.Select(attrs={'class': 'form-control'}),
            'linked_control': forms.Select(attrs={'class': 'form-control'}),
            'linked_cve': forms.Select(attrs={'class': 'form-control'}),
            'linked_vendor': forms.Select(attrs={'class': 'form-control'}),
            'mitigation_status': forms.Select(attrs={'class': 'form-control'}),
            'mitigation_plan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            from compliance.models import Control
            from vendors.models import Vendor
            from core.models import User
            self.fields['linked_control'].queryset = Control.objects.filter(organization=organization)
            self.fields['linked_vendor'].queryset = Vendor.objects.filter(organization=organization)
            self.fields['assigned_to'].queryset = User.objects.filter(organization=organization)
