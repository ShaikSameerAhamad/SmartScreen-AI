from django.contrib import admin

# Register your models here.
from .models import JobDescription, Resume, AnalysisResult

# Register your models here.
admin.site.register(JobDescription)
admin.site.register(Resume)
admin.site.register(AnalysisResult)