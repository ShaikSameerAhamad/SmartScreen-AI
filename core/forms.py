
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Resume, JobDescription # Add JobDescription import

# ... (RegistrationForm should already be here) ...
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


# ADD THE NEW FORM BELOW
class ResumeUploadForm(forms.ModelForm):
    job_description = forms.ModelChoiceField(
        queryset=JobDescription.objects.all(),
        empty_label="Select a Job Role",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Resume
        fields = ['resume_file', 'job_description']
        widgets = {
            'resume_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
