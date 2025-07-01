# core/admin.py

from django.contrib import admin
from .models import JobRole, Resume, AnalysisResult

class JobRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'required_skills')
    search_fields = ('name',)

class AnalysisResultAdmin(admin.ModelAdmin):
    # This line is now corrected to use 'improvement_score'
    list_display = ('resume', 'job_role', 'match_score', 'improvement_score', 'analyzed_at')
    list_filter = ('job_role', 'analyzed_at')

admin.site.register(JobRole, JobRoleAdmin)
admin.site.register(Resume)
admin.site.register(AnalysisResult, AnalysisResultAdmin)