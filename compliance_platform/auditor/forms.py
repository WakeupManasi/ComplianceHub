from django import forms
from .models import Audit, AuditFinding
from compliance.models import ComplianceFramework, Control
from core.models import User


class AuditForm(forms.ModelForm):
    class Meta:
        model = Audit
        fields = [
            'title', 'audit_type', 'framework', 'scope', 'objectives',
            'scheduled_start', 'scheduled_end', 'lead_auditor',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'e.g. Q2 2026 SOC 2 Audit',
            }),
            'audit_type': forms.Select(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            }),
            'framework': forms.Select(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            }),
            'scope': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'rows': 3,
                'placeholder': 'Describe the areas and controls to be audited...',
            }),
            'objectives': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'rows': 3,
                'placeholder': 'Define the objectives of this audit...',
            }),
            'scheduled_start': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            }),
            'scheduled_end': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            }),
            'lead_auditor': forms.Select(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            }),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['lead_auditor'].queryset = User.objects.filter(organization=organization)
            self.fields['framework'].queryset = ComplianceFramework.objects.filter(
                controls__organization=organization
            ).distinct()
        self.fields['framework'].required = False
        self.fields['lead_auditor'].required = False
        self.fields['framework'].empty_label = '-- Select Framework (optional) --'
        self.fields['lead_auditor'].empty_label = '-- Select Lead Auditor (optional) --'

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('scheduled_start')
        end = cleaned_data.get('scheduled_end')
        if start and end and end < start:
            raise forms.ValidationError('Scheduled end date must be after the start date.')
        return cleaned_data


class AuditFindingForm(forms.ModelForm):
    class Meta:
        model = AuditFinding
        fields = [
            'title', 'description', 'severity', 'control', 'evidence',
            'corrective_action', 'due_date', 'assigned_to',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'Finding title...',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'rows': 4,
                'placeholder': 'Describe the finding in detail...',
            }),
            'severity': forms.Select(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            }),
            'control': forms.Select(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            }),
            'evidence': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'rows': 3,
                'placeholder': 'Supporting evidence...',
            }),
            'corrective_action': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'rows': 3,
                'placeholder': 'Recommended corrective actions...',
            }),
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            }),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['assigned_to'].queryset = User.objects.filter(organization=organization)
            self.fields['control'].queryset = Control.objects.filter(organization=organization)
        self.fields['control'].required = False
        self.fields['assigned_to'].required = False
        self.fields['due_date'].required = False
        self.fields['evidence'].required = False
        self.fields['corrective_action'].required = False
        self.fields['control'].empty_label = '-- Select Control (optional) --'
        self.fields['assigned_to'].empty_label = '-- Assign to (optional) --'
