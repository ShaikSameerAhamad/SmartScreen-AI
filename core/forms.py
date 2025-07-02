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
        empty_label="-- Select a Saved Role --",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Option A: Select a Saved Role",
        required=False 
    )

    # Add the new text area for custom job descriptions
    custom_job_description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Or paste the full job description here...'}),
        label="Option B: Paste Job Description",
        required=False
    )

    class Meta:
        model = Resume
        # The form is now responsible for resume_file, job_role, and custom_job_description
        fields = ['resume_file', 'job_role', 'custom_job_description'] 
        widgets = {
            'resume_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'resume_file': '1. Upload Resume'
        }

    # Add custom validation logic
    def clean(self):
        cleaned_data = super().clean()
        job_role = cleaned_data.get("job_role")
        custom_jd = cleaned_data.get("custom_job_description")

        if not job_role and not custom_jd:
            raise ValidationError("You must either select a job role or paste a custom job description.", code='required')
        
        if job_role and custom_jd:
            raise ValidationError("Please either select a job role OR paste a custom description, not both.", code='invalid')

        return cleaned_data

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