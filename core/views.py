# core/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ResumeUploadForm, RegistrationForm
from .models import AnalysisResult, JobRole,LearningResource
from .utils.analysis import extract_text, perform_full_analysis
# Make sure all other necessary imports like login, logout, etc., are present
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from .utils.pdf_generator import render_to_pdf
from datetime import datetime

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(); login(request, user)
            return redirect('dashboard')
    else: form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data.get('username'), password=form.cleaned_data.get('password'))
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else: form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')



@login_required
def dashboard_view(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # --- THIS IS THE CORRECTED LOGIC ---
            job_role_instance = form.cleaned_data.get('job_role')
            custom_jd_text = form.cleaned_data.get('custom_job_description')
            
            # Prepare arguments for the analysis function
            job_skills_text = ""
            full_jd_text = ""
            
            if job_role_instance:
                # For predefined roles, use the specific fields from the model
                job_skills_text = job_role_instance.required_skills
                full_jd_text = job_role_instance.full_description
            elif custom_jd_text:
                # For custom roles, the skill list and full description are the same text
                job_skills_text = custom_jd_text
                full_jd_text = custom_jd_text
            # --- END CORRECTED LOGIC ---

            resume_instance = form.save(commit=False)
            resume_instance.user = request.user
            
            uploaded_file = request.FILES['resume_file']
            extracted_text = extract_text(uploaded_file)
            resume_instance.extracted_text = extracted_text
            resume_instance.save()

            # Call the analysis function with all required arguments
            analysis_data = perform_full_analysis(extracted_text, job_skills_text, full_jd_text)

            # --- Logic to calculate improvement score ---
            improvement_score = None
            if job_role_instance:
                previous_analysis = AnalysisResult.objects.filter(
                    resume__user=request.user,
                    job_role=job_role_instance
                ).order_by('-analyzed_at').first()
                if previous_analysis:
                    improvement_score = analysis_data['match_score'] - previous_analysis.match_score
            
            # Create the final result object
            result = AnalysisResult.objects.create(
                resume=resume_instance,
                job_role=job_role_instance,
                custom_job_description=custom_jd_text,
                match_score=analysis_data['match_score'],
                matched_skills=analysis_data['matched_skills'],
                missing_skills=analysis_data['missing_skills'],
                ai_suggestions=analysis_data['ai_suggestions'],
                categorized_analysis=analysis_data['categorized_analysis'],
                resume_grade=analysis_data['resume_grade'],
                grading_feedback=analysis_data['grading_feedback'],
                improvement_score=improvement_score
            )
            return redirect('results', result_id=result.id)
    else:
        form = ResumeUploadForm()
    
    all_roles = JobRole.objects.order_by('category', 'name')
    grouped_roles = {}
    uncategorized_key = "Other Roles" 
    for role in all_roles:
        category_key = role.category if role.category and role.category.strip() else uncategorized_key
        if category_key not in grouped_roles: grouped_roles[category_key] = []
        grouped_roles[category_key].append(role)
    past_results = AnalysisResult.objects.filter(resume__user=request.user).order_by('-analyzed_at')
    context = {'form': form, 'past_results': past_results, 'grouped_roles': grouped_roles}
    return render(request, 'dashboard.html', context)

@login_required
def results_view(request, result_id):
    try:
        result = AnalysisResult.objects.get(id=result_id, resume__user=request.user)
    except AnalysisResult.DoesNotExist:
        return redirect('dashboard')

    # --- NEW: Fetch Learning Resources for Missing Skills ---
    missing_skills_list = result.missing_skills
    # Create a dictionary mapping each missing skill to its LearningResource object
    learning_resources = {
        resource.skill_name: resource 
        for resource in LearningResource.objects.filter(skill_name__in=missing_skills_list)
    }
    # --- END: New Logic ---

    context = {
        'result': result,
        'learning_resources': learning_resources, # Pass new data to the template
    }
    return render(request, 'results.html', context)
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