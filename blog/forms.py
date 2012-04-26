from django import forms
from blog.models import Entry

class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ('title', 'content')
