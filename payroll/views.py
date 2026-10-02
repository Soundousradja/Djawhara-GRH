from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from accounts.decorators import role_required
from accounts.models import Profile, log_action
from employees.models import Workshop
from .models import PayrollElement
from .forms import PayrollElementForm, BonusFormSet, DeductionFormSet


@role_required(Profile.ROLE_RH, Profile.ROLE_COMPTABLE, Profile.ROLE_GERANT)
def payroll_list(request):
    elements = PayrollElement.objects.select_related('employee', 'employee__workshop').all()
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')
    workshop_id = request.GET.get('workshop', '')
    if month:
        elements = elements.filter(month=month)
    if year:
        elements = elements.filter(year=year)
    if workshop_id:
        elements = elements.filter(employee__workshop_id=workshop_id)

    total_net = sum((e.net_pay for e in elements), start=0)

    context = {
        'elements': elements,
        'total_net': total_net,
        'workshops': Workshop.objects.all(),
        'selected_workshop': workshop_id,
        'filters': request.GET,
        'active_menu': 'payroll',
    }
    return render(request, 'payroll/payroll_list.html', context)


@role_required(Profile.ROLE_RH, Profile.ROLE_GERANT)
def payroll_create(request):
    if request.method == 'POST':
        form = PayrollElementForm(request.POST)
        if form.is_valid():
            payroll = form.save(commit=False)
            payroll.save()
            bonus_fs = BonusFormSet(request.POST, instance=payroll)
            deduction_fs = DeductionFormSet(request.POST, instance=payroll)
            if bonus_fs.is_valid() and deduction_fs.is_valid():
                bonus_fs.save()
                deduction_fs.save()
                payroll.recalculate()
                payroll.save()
                log_action(request.user, 'CREATE', payroll)
                messages.success(request, "Élément de paie enregistré.")
                return redirect('payroll_detail', pk=payroll.pk)
        else:
            bonus_fs = BonusFormSet(request.POST)
            deduction_fs = DeductionFormSet(request.POST)
    else:
        form = PayrollElementForm()
        bonus_fs = BonusFormSet()
        deduction_fs = DeductionFormSet()
    return render(request, 'payroll/payroll_form.html', {
        'form': form, 'bonus_fs': bonus_fs, 'deduction_fs': deduction_fs,
        'active_menu': 'payroll',
    })


@role_required(Profile.ROLE_RH, Profile.ROLE_COMPTABLE, Profile.ROLE_GERANT)
def payroll_detail(request, pk):
    payroll = get_object_or_404(PayrollElement, pk=pk)
    context = {
        'payroll': payroll,
        'bonuses': payroll.bonuses.all(),
        'deductions': payroll.deductions.all(),
        'active_menu': 'payroll',
    }
    return render(request, 'payroll/payroll_detail.html', context)


@role_required(Profile.ROLE_RH, Profile.ROLE_COMPTABLE, Profile.ROLE_GERANT)
def payroll_print(request, pk):
    payroll = get_object_or_404(
        PayrollElement.objects.select_related('employee', 'employee__workshop'),
        pk=pk,
    )
    return render(request, 'payroll/payroll_print.html', {
        'payroll': payroll,
        'bonuses': payroll.bonuses.all(),
        'deductions': payroll.deductions.all(),
    })


@role_required(Profile.ROLE_RH, Profile.ROLE_GERANT)
def payroll_update(request, pk):
    payroll = get_object_or_404(PayrollElement, pk=pk)
    if request.method == 'POST':
        form = PayrollElementForm(request.POST, instance=payroll)
        bonus_fs = BonusFormSet(request.POST, instance=payroll)
        deduction_fs = DeductionFormSet(request.POST, instance=payroll)
        if form.is_valid() and bonus_fs.is_valid() and deduction_fs.is_valid():
            payroll = form.save()
            bonus_fs.save()
            deduction_fs.save()
            payroll.recalculate()
            payroll.save()
            log_action(request.user, 'UPDATE', payroll)
            messages.success(request, "Élément de paie mis à jour.")
            return redirect('payroll_detail', pk=payroll.pk)
    else:
        form = PayrollElementForm(instance=payroll)
        bonus_fs = BonusFormSet(instance=payroll)
        deduction_fs = DeductionFormSet(instance=payroll)
    return render(request, 'payroll/payroll_form.html', {
        'form': form, 'bonus_fs': bonus_fs, 'deduction_fs': deduction_fs,
        'payroll': payroll, 'active_menu': 'payroll',
    })


@role_required(Profile.ROLE_RH, Profile.ROLE_GERANT)
def payroll_delete(request, pk):
    payroll = get_object_or_404(PayrollElement, pk=pk)
    if request.method == 'POST':
        employee_name = payroll.employee.full_name
        log_action(request.user, 'DELETE', payroll)
        payroll.delete()
        messages.success(request, f"La fiche de paie de {employee_name} a été supprimée.")
        return redirect('payroll_list')
    return redirect('payroll_detail', pk=payroll.pk)
