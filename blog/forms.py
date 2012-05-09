from django import forms
from blog.models import Post

class EntryForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'content')
