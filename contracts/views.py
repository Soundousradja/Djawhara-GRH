from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from accounts.decorators import role_required
from accounts.models import Profile, log_action
from .models import Contract
from .forms import ContractForm


@login_required
def contract_list(request):
    contracts = Contract.objects.select_related('employee', 'employee__workshop').all()

    status = request.GET.get('status', '')
    contract_type = request.GET.get('type', '')
    if status:
        contracts = contracts.filter(status=status)
    if contract_type:
        contracts = contracts.filter(contract_type=contract_type)

    ending_soon = [c for c in Contract.objects.filter(status=Contract.STATUS_ACTIVE) if c.is_ending_soon]

    context = {
        'contracts': contracts,
        'ending_soon': ending_soon,
        'status_choices': Contract.STATUS_CHOICES,
        'type_choices': Contract.TYPE_CHOICES,
        'filters': request.GET,
        'active_menu': 'contracts',
    }
    return render(request, 'contracts/contract_list.html', context)


@role_required(Profile.ROLE_RH)
def contract_create(request):
    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES)
        if form.is_valid():
            contract = form.save()
            log_action(request.user, 'CREATE', contract)
            messages.success(request, "Contrat enregistré.")
            return redirect('contract_list')
    else:
        form = ContractForm(initial={'employee': request.GET.get('employee')})
    return render(request, 'contracts/contract_form.html', {'form': form, 'active_menu': 'contracts'})


@role_required(Profile.ROLE_RH)
def contract_update(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES, instance=contract)
        if form.is_valid():
            form.save()
            log_action(request.user, 'UPDATE', contract)
            messages.success(request, "Contrat mis à jour.")
            return redirect('contract_list')
    else:
        form = ContractForm(instance=contract)
    return render(request, 'contracts/contract_form.html',
                  {'form': form, 'contract': contract, 'active_menu': 'contracts'})


@role_required(Profile.ROLE_RH)
def contract_delete(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == 'POST':
        employee_name = contract.employee.full_name
        log_action(request.user, 'DELETE', contract)
        contract.delete()
        messages.success(request, f"Le contrat de {employee_name} a été supprimé.")
        return redirect('contract_list')
    return redirect('contract_list')
