from django.db import models

# Create your models here.
from django.contrib.auth.models import User

class JobDescription(models.Model):
    title = models.CharField(max_length=200, unique=True)
    description_text = models.TextField()
    required_skills = models.JSONField(default=list, blank=True) 

    def __str__(self):
        return self.title

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resume_file = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Resume for {self.user.username} uploaded at {self.uploaded_at.strftime('%Y-%m-%d')}"

class AnalysisResult(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    job_description = models.ForeignKey(JobDescription, on_delete=models.CASCADE)
    match_score = models.FloatField(default=0.0)
    missing_skills = models.JSONField(default=list)
    ai_suggestions = models.TextField(blank=True, null=True)
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.resume.user.username} vs {self.job_description.title}"
