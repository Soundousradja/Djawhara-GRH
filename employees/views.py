from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from accounts.decorators import role_required
from accounts.models import Profile, log_action
from .models import Employee, EmployeeDocument, Workshop
from .forms import EmployeeForm, EmployeeDocumentForm, WorkshopForm


@login_required
def employee_list(request):
    employees = Employee.objects.select_related('workshop').all()

    profile = getattr(request.user, 'profile', None)
    if profile and profile.is_chef and profile.workshop:
        employees = employees.filter(workshop=profile.workshop)

    q = request.GET.get('q', '').strip()
    workshop_id = request.GET.get('workshop', '')
    status = request.GET.get('status', '')
  

    if q:
        employees = employees.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(position__icontains=q) | Q(national_id__icontains=q)
        )
    if workshop_id:
        employees = employees.filter(workshop_id=workshop_id)
    if status:
        employees = employees.filter(status=status)

    paginator = Paginator(employees, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'workshops': Workshop.objects.all(),
        'status_choices': Employee.STATUS_CHOICES,
        'q': q,
        'selected_workshop': workshop_id,
        'selected_status': status,
        'active_menu': 'employees',
    }
    return render(request, 'employees/employee_list.html', context)


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee.objects.select_related('workshop'), pk=pk)
    doc_form = EmployeeDocumentForm()
    context = {
        'employee': employee,
        'contracts': employee.contracts.order_by('-start_date'),
        'attendance_records': employee.attendance_records.order_by('-date')[:30],
        'payroll_elements': employee.payroll_elements.order_by('-year', '-month')[:12],
        'documents': employee.documents.all(),
        'doc_form': doc_form,
        'active_menu': 'employees',
    }
    return render(request, 'employees/employee_detail.html', context)


@role_required(Profile.ROLE_RH)
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save()
            log_action(request.user, 'CREATE', employee)
            messages.success(request, "Fiche employé créée avec succès.")
            return redirect('employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'active_menu': 'employees'})


@role_required(Profile.ROLE_RH)
def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            log_action(request.user, 'UPDATE', employee)
            messages.success(request, "Fiche employé mise à jour.")
            return redirect('employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'employees/employee_form.html',
                  {'form': form, 'employee': employee, 'active_menu': 'employees'})


@role_required(Profile.ROLE_RH)
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee_name = employee.full_name
        log_action(request.user, 'DELETE', employee)
        employee.delete()
        messages.success(request, f"L'employé {employee_name} a été supprimé.")
        return redirect('employee_list')
    return redirect('employee_detail', pk=employee.pk)


@role_required(Profile.ROLE_RH)
def employee_add_document(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.employee = employee
            doc.save()
            log_action(request.user, 'CREATE', doc)
            messages.success(request, "Document ajouté.")
    return redirect('employee_detail', pk=employee.pk)


@login_required
def workshop_list(request):
    workshops = Workshop.objects.all()
    profile = getattr(request.user, 'profile', None)
    can_manage = request.user.is_superuser or (profile and profile.can_manage_employees)

    if request.method == 'POST':
        if not can_manage:
            messages.error(request, "Vous n'avez pas la permission d'ajouter un atelier.")
            return redirect('workshop_list')
        form = WorkshopForm(request.POST)
        if form.is_valid():
            workshop = form.save()
            log_action(request.user, 'CREATE', workshop)
            messages.success(request, "Atelier ajouté.")
            return redirect('workshop_list')
    else:
        form = WorkshopForm()
    return render(request, 'employees/workshop_list.html',
                  {'workshops': workshops, 'form': form, 'can_manage': can_manage, 'active_menu': 'workshops'})

@login_required
def incomplete_files(request):
    employees = (
        Employee.objects
        .filter(status=Employee.STATUS_ACTIVE)
        .select_related('workshop')
        .prefetch_related('documents')
    )

    incomplete = []

    for employee in employees:
        try:
            missing = employee.missing_documents
        except Exception:
            missing = []

        if missing:
            incomplete.append({
                'employee': employee,
                'missing_count': len(missing),
                'missing_documents': missing,
            })

    incomplete.sort(
        key=lambda x: x['missing_count'],
        reverse=True
    )

    context = {
        'incomplete_files': incomplete,
        'active_menu': 'employees',
    }

    return render(
        request,
        'employees/incomplete_files.html',
        context
    )