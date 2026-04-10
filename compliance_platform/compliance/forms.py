from django import forms
from .models import Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'doc_type', 'file', 'controls', 'storage_link']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'doc_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'controls': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '8'}),
            'storage_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['controls'].queryset = (
                self.fields['controls'].queryset.filter(organization=organization)
            )
