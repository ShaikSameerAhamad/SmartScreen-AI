# core/models.py

from django.db import models
from django.contrib.auth.models import User

class JobRole(models.Model):
    name = models.CharField(max_length=100, unique=True)
    required_skills = models.TextField(
        help_text="Enter skills separated by commas, e.g., Python, Django, REST API"
    )

    def get_skills_list(self):
        """Returns a clean list of lowercased skills."""
        return [skill.strip().lower() for skill in self.required_skills.split(',') if skill.strip()]

    def __str__(self):
        return self.name

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resume_file = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Resume for {self.user.username} uploaded at {self.uploaded_at.strftime('%Y-%m-%d')}"

class AnalysisResult(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    job_role = models.ForeignKey(JobRole, on_delete=models.CASCADE) # No longer optional
    match_score = models.FloatField(default=0.0)
    missing_skills = models.JSONField(default=list)
    ai_suggestions = models.TextField(blank=True, null=True)
    resume_grade = models.FloatField(default=0.0)
    grading_feedback = models.JSONField(default=dict)
    rewritten_resume_text = models.TextField(blank=True, null=True)
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.resume.user.username} vs {self.job_role.name}"