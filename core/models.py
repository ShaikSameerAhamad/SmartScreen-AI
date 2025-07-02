from django.db import models
from django.contrib.auth.models import User

class JobRole(models.Model):
    name = models.CharField(max_length=100, unique=True)
    # NEW: Add a category for grouping in the UI
    category = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Back-End Developer, Data Scientist")
    # This field will now store the full, detailed job description
    full_description = models.TextField(
        help_text="Paste the full, detailed job description here. This will be sent to the AI for analysis."
    )

    # This field will still be used for skill matching and categorical analysis
    required_skills = models.TextField(
        help_text="Enter a comma-separated list of the most important skills for this role."
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
    job_role = models.ForeignKey(JobRole, on_delete=models.CASCADE, null=True, blank=True)
    
    # Add a field to store the text of a custom job description
    custom_job_description = models.TextField(blank=True, null=True)
    
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
    def get_job_title(self):
        """Returns the job title, whether from a saved role or a custom one."""
        if self.job_role:
            return self.job_role.name
        return "Custom Job Description"
    
    def __str__(self):
        return f"Analysis for {self.resume.user.username} vs {self.job_role.name} on {self.analyzed_at.date()}"
