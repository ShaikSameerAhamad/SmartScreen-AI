from django.db import models
from django.contrib.auth.models import User

class JobRole(models.Model):
    name = models.CharField(max_length=100, unique=True)
    required_skills = models.TextField(
        help_text="Enter skills separated by commas, e.g., Python, Django, REST API"
    )

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
    job_role = models.ForeignKey(JobRole, on_delete=models.CASCADE)
    
    # Scores and Analysis Data
    match_score = models.FloatField(default=0.0)
    matched_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    categorized_analysis = models.JSONField(default=dict)
    
    # Resume Grading Data (for first-time analysis)
    resume_grade = models.FloatField(default=0.0)
    grading_feedback = models.JSONField(default=dict)

    # Improvement Score Data (for subsequent analyses)
    improvement_score = models.FloatField(null=True, blank=True)
    
    # AI Suggestions and Timestamps
    ai_suggestions = models.TextField(blank=True, null=True)
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.resume.user.username} vs {self.job_role.name} on {self.analyzed_at.date()}"
