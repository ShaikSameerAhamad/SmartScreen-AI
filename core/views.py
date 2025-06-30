from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, ResumeUploadForm # Import new form
from .models import Resume, JobDescription, AnalysisResult # Import models
from .analyzer import extract_text_from_file, analyze_resume # Import analyzer functions

# ... (register_view, login_view, logout_view are unchanged) ...
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


# MODIFY THE DASHBOARD VIEW
@login_required
def dashboard_view(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # 1. Save resume file and get object
            resume_instance = form.save(commit=False)
            resume_instance.user = request.user
            resume_instance.save()

            # 2. Extract text from the saved file
            file_path = resume_instance.resume_file.path
            extracted_text = extract_text_from_file(file_path)
            resume_instance.extracted_text = extracted_text
            resume_instance.save()

            # 3. Get Job Description
            job_desc = form.cleaned_data['job_description']

            # 4. Run Analysis (using our placeholder function for now)
            analysis_data = analyze_resume(extracted_text, job_desc.description_text)

            # 5. Save Analysis Result
            result = AnalysisResult.objects.create(
                resume=resume_instance,
                job_description=job_desc,
                match_score=analysis_data['match_score'],
                missing_skills=analysis_data['missing_skills'],
                ai_suggestions=analysis_data['ai_suggestions']
            )
            
            # Redirect to the new results page
            return redirect('results', result_id=result.id)
    else:
        form = ResumeUploadForm()
    
    # Fetch previous results for the user to display on the dashboard
    past_results = AnalysisResult.objects.filter(resume__user=request.user).order_by('-analyzed_at')

    context = {
        'form': form,
        'past_results': past_results
    }
    return render(request, 'dashboard.html', context)

# ADD THE NEW RESULTS VIEW
@login_required
def results_view(request, result_id):
    try:
        result = AnalysisResult.objects.get(id=result_id, resume__user=request.user)
    except AnalysisResult.DoesNotExist:
        return redirect('dashboard') # Or show a 404 error

    context = {
        'result': result
    }
    return render(request, 'results.html', context)
