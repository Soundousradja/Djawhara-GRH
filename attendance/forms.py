from django import forms
from employees.forms import StyledFormMixin
from .models import AttendanceRecord, DisciplinaryAction


class AttendanceRecordForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ['status', 'minutes_late', 'note']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class DisciplinaryActionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = DisciplinaryAction
        fields = ['action_type', 'reason', 'date']
        widgets = {'date': forms.DateInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
