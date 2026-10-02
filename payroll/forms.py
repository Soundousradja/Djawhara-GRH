from django import forms
from django.forms import inlineformset_factory
from employees.forms import StyledFormMixin
from .models import PayrollElement, Bonus, Deduction


class PayrollElementForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = PayrollElement
        fields = [
            'employee', 'month', 'year', 'advance', 'status', 'notes',
        ]
        widgets = {'notes': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class BonusForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Bonus
        fields = ['label', 'amount']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class DeductionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Deduction
        fields = ['label', 'amount']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


BonusFormSet = inlineformset_factory(
    PayrollElement, Bonus, form=BonusForm, extra=1, can_delete=True
)
DeductionFormSet = inlineformset_factory(
    PayrollElement, Deduction, form=DeductionForm, extra=1, can_delete=True
)
