from django import forms
from employees.forms import StyledFormMixin
from .models import Contract


class ContractForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            'employee', 'contract_type', 'start_date', 'end_date',
            'payment_method', 'base_salary', 'status', 'document', 'notes',
        ]
        widgets = {
            'start_date': forms.DateInput(),
            'end_date': forms.DateInput(),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
