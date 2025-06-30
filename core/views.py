# core/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, ResumeUploadForm
from django.http import HttpResponse
from .models import Resume, JobRole, AnalysisResult
from .utils.analysis import extract_text, perform_full_analysis
from .utils.pdf_generator import render_to_pdf # <-- IMPORT NEW UTILITY
from datetime import datetime # Import datetime

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume_instance = form.save(commit=False)
            resume_instance.user = request.user
            resume_instance.save()

            # --- THIS IS THE KEY CHANGE ---
            # We now pass the file object directly from the form, not the file path
            uploaded_file = request.FILES['resume_file']
            extracted_text = extract_text(uploaded_file)
            # --- END OF CHANGE ---

            resume_instance.extracted_text = extracted_text
            resume_instance.save()

            job_role = form.cleaned_data['job_role']
            analysis_data = perform_full_analysis(extracted_text, job_role)

            result = AnalysisResult.objects.create(
                resume=resume_instance,
                job_role=job_role,
                match_score=analysis_data['match_score'],
                missing_skills=analysis_data['missing_skills'],
                ai_suggestions=analysis_data['ai_suggestions'],
                resume_grade=analysis_data['resume_grade'],
                grading_feedback=analysis_data['grading_feedback']
            )
            
            return redirect('results', result_id=result.id)
    else:
        form = ResumeUploadForm()
    
    past_results = AnalysisResult.objects.filter(resume__user=request.user).order_by('-analyzed_at')
    context = {'form': form, 'past_results': past_results}
    return render(request, 'dashboard.html', context)

@login_required
def results_view(request, result_id):
    try:
        result = AnalysisResult.objects.get(id=result_id, resume__user=request.user)
    except AnalysisResult.DoesNotExist:
        return redirect('dashboard')

    context = {
        'result': result
    }
    return render(request, 'results.html', context)
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')



@login_required
def results_view(request, result_id):
    try:
        result = AnalysisResult.objects.get(id=result_id, resume__user=request.user)
    except AnalysisResult.DoesNotExist:
        return redirect('dashboard')
    context = {'result': result}
    return render(request, 'results.html', context)

# ADD THE CORRECTED DOWNLOAD VIEW
@login_required
def download_pdf_view(request, result_id):
    try:
        result = AnalysisResult.objects.get(id=result_id, resume__user=request.user)
    except AnalysisResult.DoesNotExist:
        return redirect('dashboard')

    context = {'result': result}
    pdf = render_to_pdf('pdf_template.html', context)
    
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"resume_feedback_{datetime.now().strftime('%Y-%m-%d')}.pdf"
        content = f"attachment; filename={filename}"
        response['Content-Disposition'] = content
        return response
    
    return HttpResponse("PDF generation failed.", status=500)

@login_required
def download_pdf_view(request, result_id):
    try:
        result = AnalysisResult.objects.get(id=result_id, resume__user=request.user)
    except AnalysisResult.DoesNotExist:
        return redirect('dashboard')

    context = {'result': result}
    pdf = render_to_pdf('pdf_template.html', context)
    
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"resume_feedback_{datetime.now().strftime('%Y-%m-%d')}.pdf"
        content = f"attachment; filename={filename}"
        response['Content-Disposition'] = content
        return response
    
    return HttpResponse("Not found")

