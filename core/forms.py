# core/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Resume, JobRole
import os

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class ResumeUploadForm(forms.ModelForm):
    job_role = forms.ModelChoiceField(
        queryset=JobRole.objects.all(),
        empty_label="-- Select a Job Role --",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Target Job Role",
        required=True # It is now required
    )

    class Meta:
        model = Resume
        fields = ['resume_file', 'job_role']
        widgets = {
            'resume_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_resume_file(self):
        file = self.cleaned_data.get('resume_file', False)
        if file:
            if file.size > 5 * 1024 * 1024:
                raise ValidationError("File size exceeds 5MB limit.")
            allowed_extensions = ['.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png']
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(f"Unsupported file extension '{ext}'. Allowed types: PDF, DOCX, TXT, JPG, PNG.")
        return file