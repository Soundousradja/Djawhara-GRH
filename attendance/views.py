import datetime
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Count, Q

from accounts.models import Profile, log_action
from employees.models import Employee, Workshop

from .models import AttendanceRecord, DisciplinaryAction
from .forms import DisciplinaryActionForm


def _visible_workshops(request):
    """
    Retourne les ateliers visibles par l'utilisateur.

    - RH / administrateur : tous les ateliers
    - Chef d'atelier : uniquement son atelier
    """
    profile = getattr(request.user, 'profile', None)

    workshops = Workshop.objects.all()

    if profile and profile.is_chef and profile.workshop:
        workshops = workshops.filter(pk=profile.workshop_id)

    return workshops


@login_required
def daily_entry(request):
    """
    Page de pointage quotidien.
    Le chef d'atelier ne peut voir que les employés de son atelier.
    """

    workshops = _visible_workshops(request)

    # Récupération de la date
    date_str = request.GET.get('date')

    try:
        selected_date = (
            datetime.date.fromisoformat(date_str)
            if date_str
            else datetime.date.today()
        )
    except ValueError:
        selected_date = datetime.date.today()

    # Atelier sélectionné
    workshop_id = request.GET.get('workshop')

    if not workshop_id and workshops.exists():
        workshop_id = workshops.first().pk

    # Employés actifs
    employees = Employee.objects.filter(
        status=Employee.STATUS_ACTIVE
    )

    # Filtrage par atelier
    if workshop_id:
        employees = employees.filter(
            workshop_id=workshop_id
        )

    # Récupération des pointages existants
    existing = {
        record.employee_id: record
        for record in AttendanceRecord.objects.filter(
            date=selected_date,
            employee__in=employees
        )
    }

    # Préparation des lignes
    rows = []

    for employee in employees.order_by('last_name', 'first_name'):
        rows.append({
            'employee': employee,
            'record': existing.get(employee.id)
        })

    context = {
        'workshops': workshops,
        'selected_workshop': int(workshop_id) if workshop_id else None,
        'selected_date': selected_date,
        'rows': rows,
        'status_choices': AttendanceRecord.STATUS_CHOICES,
        'active_menu': 'attendance',
    }

    return render(
        request,
        'attendance/daily_entry.html',
        context
    )


@login_required
def daily_attendance_print(request):
    """Liste imprimable des pointages pour une date et un atelier."""
    workshops = _visible_workshops(request)
    date_str = request.GET.get('date')

    try:
        selected_date = (
            datetime.date.fromisoformat(date_str)
            if date_str
            else datetime.date.today()
        )
    except ValueError:
        selected_date = datetime.date.today()

    workshop_id = request.GET.get('workshop')
    if not workshop_id and workshops.exists():
        workshop_id = workshops.first().pk

    selected_workshop = workshops.filter(pk=workshop_id).first()
    employees = Employee.objects.filter(status=Employee.STATUS_ACTIVE)
    if workshop_id and not selected_workshop:
        employees = employees.none()
    elif selected_workshop:
        employees = employees.filter(workshop=selected_workshop)

    employees = employees.select_related('workshop').order_by('last_name', 'first_name')
    records = {
        record.employee_id: record
        for record in AttendanceRecord.objects.filter(
            date=selected_date,
            employee__in=employees,
        )
    }
    rows = [
        {
            'employee': employee,
            'record': records.get(employee.id),
        }
        for employee in employees
    ]

    return render(
        request,
        'attendance/daily_print.html',
        {
            'rows': rows,
            'selected_date': selected_date,
            'selected_workshop': selected_workshop,
        },
    )


@login_required
@require_POST
def save_attendance(request):
    """
    Enregistre ou modifie un pointage via JavaScript / fetch.
    """

    profile = getattr(request.user, 'profile', None)

    try:
        payload = json.loads(
            request.body.decode('utf-8')
        )

        employee_id = int(
            payload['employee_id']
        )

        date_val = datetime.date.fromisoformat(
            payload['date']
        )

        status = payload['status']

        minutes_late = int(
            payload.get('minutes_late') or 0
        )

        note = payload.get(
            'note',
            ''
        )

    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse(
            {
                'ok': False,
                'error': 'Données invalides.'
            },
            status=400
        )

    # Vérification de l'employé
    employee = get_object_or_404(
        Employee,
        pk=employee_id
    )

    # Sécurité chef d'atelier
    if (
        profile
        and profile.is_chef
        and profile.workshop_id
        and employee.workshop_id != profile.workshop_id
    ):
        return JsonResponse(
            {
                'ok': False,
                'error': (
                    "Vous ne pouvez pointer que "
                    "les employés de votre atelier."
                )
            },
            status=403
        )

    # Vérification du statut
    valid_statuses = [
        choice[0]
        for choice in AttendanceRecord.STATUS_CHOICES
    ]

    if status not in valid_statuses:
        return JsonResponse(
            {
                'ok': False,
                'error': 'Statut de pointage invalide.'
            },
            status=400
        )

    # Création ou modification
    record, created = AttendanceRecord.objects.update_or_create(
        employee=employee,
        date=date_val,
        defaults={
            'status': status,
            'minutes_late': minutes_late,
            'note': note,
            'workshop': employee.workshop,
            'recorded_by': request.user,
            'source': AttendanceRecord.SOURCE_MANUAL,
        }
    )

    # Journalisation
    log_action(
        request.user,
        'CREATE' if created else 'UPDATE',
        record
    )

    return JsonResponse(
        {
            'ok': True,
            'created': created,
            'record_id': record.id,
            'status': record.status,
            'status_display': record.get_status_display(),
        }
    )


def _register_biometric_punch(biometric_id, direction='IN', occurred_at=None, user=None):
    """Enregistre un passage transmis par une borne ou un lecteur d'empreintes."""
    employee = Employee.objects.filter(
        biometric_id=biometric_id,
        status=Employee.STATUS_ACTIVE,
    ).select_related('workshop').first()
    if not employee:
        return None, 'Empreinte inconnue ou employe inactif.'

    occurred_at = occurred_at or timezone.now()
    local_time = timezone.localtime(occurred_at)
    record, created = AttendanceRecord.objects.get_or_create(
        employee=employee,
        date=local_time.date(),
        defaults={
            'workshop': employee.workshop,
            'status': AttendanceRecord.STATUS_PRESENT,
            'source': AttendanceRecord.SOURCE_BIOMETRIC,
            'check_in_at': local_time if direction == 'IN' else None,
            'check_out_at': local_time if direction == 'OUT' else None,
            'recorded_by': user,
        },
    )

    if not created:
        # Le premier passage est l'entree; les suivants sont consideres comme sortie.
        if direction == 'OUT' or record.check_in_at:
            record.check_out_at = local_time
        else:
            record.check_in_at = local_time
        record.source = AttendanceRecord.SOURCE_BIOMETRIC
        if user:
            record.recorded_by = user
        record.save(update_fields=['check_in_at', 'check_out_at', 'source', 'recorded_by'])

    return record, None


@login_required
@require_POST
def biometric_punch(request):
    """Borne interne: le lecteur renseigne l'identifiant biometrque de l'employe."""
    biometric_id = request.POST.get('biometric_id', '').strip()
    direction = request.POST.get('direction', 'IN').upper()
    if direction not in ('IN', 'OUT'):
        direction = 'IN'
    record, error = _register_biometric_punch(biometric_id, direction, user=request.user)
    if error:
        messages.error(request, error)
    else:
        log_action(request.user, 'CREATE', record)
        messages.success(request, f"Pointage par empreinte enregistre pour {record.employee.full_name}.")
    return redirect('biometric_terminal')


@login_required
def biometric_terminal(request):
    return render(request, 'attendance/biometric_terminal.html', {'active_menu': 'attendance'})


@csrf_exempt
@require_POST
def biometric_api(request):
    """API pour le logiciel du terminal biometrque (jamais d'image d'empreinte)."""
    expected_token = getattr(settings, 'BIOMETRIC_TERMINAL_TOKEN', '')
    if not expected_token or request.headers.get('X-Biometric-Token') != expected_token:
        return JsonResponse({'ok': False, 'error': 'Terminal non autorise.'}, status=403)
    try:
        payload = json.loads(request.body.decode('utf-8'))
        biometric_id = str(payload['biometric_id']).strip()
        direction = str(payload.get('direction', 'IN')).upper()
        if direction not in ('IN', 'OUT'):
            raise ValueError
        occurred_at = payload.get('occurred_at')
        occurred_at = datetime.datetime.fromisoformat(occurred_at) if occurred_at else None
        if occurred_at and timezone.is_naive(occurred_at):
            occurred_at = timezone.make_aware(occurred_at)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({'ok': False, 'error': 'Donnees invalides.'}, status=400)

    record, error = _register_biometric_punch(biometric_id, direction, occurred_at)
    if error:
        return JsonResponse({'ok': False, 'error': error}, status=404)
    return JsonResponse({'ok': True, 'record_id': record.id, 'employee': record.employee.full_name})


@login_required
def attendance_history(request):
    """
    Historique des pointages avec filtres.
    """

    records = AttendanceRecord.objects.select_related(
        'employee',
        'workshop',
        'recorded_by'
    ).all()

    profile = getattr(request.user, 'profile', None)

    # Chef d'atelier : uniquement son atelier
    if (
        profile
        and profile.is_chef
        and profile.workshop
    ):
        records = records.filter(
            workshop=profile.workshop
        )

    # Filtres
    workshop_id = request.GET.get(
        'workshop',
        ''
    )

    status = request.GET.get(
        'status',
        ''
    )

    date_from = request.GET.get(
        'date_from',
        ''
    )

    date_to = request.GET.get(
        'date_to',
        ''
    )

    # Filtre atelier
    if workshop_id:
        records = records.filter(
            workshop_id=workshop_id
        )

    # Filtre statut
    if status:
        records = records.filter(
            status=status
        )

    # Date début
    if date_from:
        records = records.filter(
            date__gte=date_from
        )

    # Date fin
    if date_to:
        records = records.filter(
            date__lte=date_to
        )

    # Limite pour éviter une page trop lourde
    records = records.order_by(
        '-date',
        'employee__last_name'
    )[:500]

    context = {
        'records': records,
        'workshops': _visible_workshops(request),
        'status_choices': AttendanceRecord.STATUS_CHOICES,
        'filters': request.GET,
        'active_menu': 'attendance',
    }

    return render(
        request,
        'attendance/history.html',
        context
    )


@login_required
def discipline_dashboard(request):
    """
    Tableau de suivi disciplinaire.

    Affiche les employés ayant :
    - des absences
    - des absences injustifiées
    - des retards
    durant les 30 derniers jours.
    """

    thirty_days_ago = (
        datetime.date.today()
        - datetime.timedelta(days=30)
    )

    profile = getattr(
        request.user,
        'profile',
        None
    )

    # Pointages problématiques
    problem_records = AttendanceRecord.objects.filter(
        date__gte=thirty_days_ago
    ).filter(
        Q(
            status=AttendanceRecord.STATUS_ABSENT_UNJUSTIFIED
        )
        |
        Q(
            status=AttendanceRecord.STATUS_ABSENT_JUSTIFIED
        )
        |
        Q(
            status=AttendanceRecord.STATUS_LATE
        )
    )

    # Chef d'atelier : seulement son atelier
    if (
        profile
        and profile.is_chef
        and profile.workshop
    ):
        problem_records = problem_records.filter(
            workshop=profile.workshop
        )

    problem_qs = (
        problem_records
        .values(
            'employee',
            'employee__first_name',
            'employee__last_name',
            'employee__workshop__name',
            'status'
        )
        .annotate(
            total=Count('id')
        )
    )

    per_employee = {}

    for row in problem_qs:

        employee_id = row['employee']

        entry = per_employee.setdefault(
            employee_id,
            {
                'employee_id': employee_id,
                'name': (
                    f"{row['employee__first_name']} "
                    f"{row['employee__last_name']}"
                ),
                'workshop': (
                    row['employee__workshop__name']
                    or '-'
                ),
                'absences': 0,
                'unjustified': 0,
                'late': 0,
            }
        )

        if row['status'] == (
            AttendanceRecord.STATUS_ABSENT_UNJUSTIFIED
        ):
            entry['unjustified'] += row['total']
            entry['absences'] += row['total']

        elif row['status'] == (
            AttendanceRecord.STATUS_ABSENT_JUSTIFIED
        ):
            entry['absences'] += row['total']

        elif row['status'] == (
            AttendanceRecord.STATUS_LATE
        ):
            entry['late'] += row['total']

    # Tri :
    # 1. absences injustifiées
    # 2. retards
    problem_employees = sorted(
        per_employee.values(),
        key=lambda employee: (
            employee['unjustified'],
            employee['late']
        ),
        reverse=True
    )

    # Actions disciplinaires
    if request.method == 'POST':

        form = DisciplinaryActionForm(
            request.POST
        )

        employee_id = request.POST.get(
            'employee_id'
        )

        if form.is_valid() and employee_id:

            # Vérification si chef d'atelier
            if (
                profile
                and profile.is_chef
                and profile.workshop
            ):
                employee = get_object_or_404(
                    Employee,
                    pk=employee_id
                )

                if (
                    employee.workshop_id
                    != profile.workshop_id
                ):
                    messages.error(
                        request,
                        "Vous ne pouvez pas créer "
                        "une action pour cet employé."
                    )

                    return redirect(
                        'discipline_dashboard'
                    )

            action = form.save(
                commit=False
            )

            action.employee_id = employee_id
            action.created_by = request.user

            action.save()

            log_action(
                request.user,
                'CREATE',
                action
            )

            messages.success(
                request,
                "Action disciplinaire enregistrée."
            )

            return redirect(
                'discipline_dashboard'
            )

    else:
        form = DisciplinaryActionForm()

    recent_actions = (
        DisciplinaryAction.objects
        .select_related(
            'employee',
            'created_by'
        )
    )

    if (
        profile
        and profile.is_chef
        and profile.workshop
    ):
        recent_actions = recent_actions.filter(
            employee__workshop=profile.workshop
        )

    recent_actions = recent_actions[:20]

    context = {
        'problem_employees': (
            problem_employees[:30]
        ),
        'recent_actions': recent_actions,
        'form': form,
        'active_menu': 'attendance',
    }

    return render(
        request,
        'attendance/discipline.html',
        context
    )
