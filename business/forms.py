from django import forms
from .models import Business

class BusinessProfileForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name', 'type']
        labels = {
            'name': 'Nama Usaha',
            'type': 'Jenis Usaha',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2'}),
            'type': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2'}),
        }
