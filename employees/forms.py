from django import forms
from .models import Employee, EmployeeDocument, Workshop


class StyledFormMixin:
    """Ajoute la classe CSS 'form-control' à tous les champs du formulaire."""

    def _style(self):
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            if isinstance(field.widget, (forms.CheckboxInput,)):
                field.widget.attrs['class'] = (existing + ' form-check-input').strip()
            else:
                field.widget.attrs['class'] = (existing + ' form-control').strip()
            if isinstance(field.widget, forms.DateInput):
                field.widget.attrs.setdefault('type', 'date')


class EmployeeForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'birth_date', 'birth_place', 'national_id',
            'address', 'phone', 'family_status', 'cnas_number', 'biometric_id', 'photo',
            'sex', 'hire_date', 'position', 'workshop', 'responsible', 'status',
        ]
        widgets = {
            'birth_date': forms.DateInput(),
            'hire_date': forms.DateInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
        self.fields['biometric_id'].help_text = (
            "Saisissez l'identifiant attribué par le terminal lors de "
            "l'enrôlement de l'empreinte. L'empreinte brute n'est jamais "
            "enregistrée dans l'application."
        )
        self.fields['biometric_id'].widget.attrs.update({
            'autocomplete': 'off',
            'placeholder': 'Ex. 100245',
        })

    def clean_biometric_id(self):
        """Normalise l'identifiant transmis par le terminal biométrique."""
        biometric_id = (self.cleaned_data.get('biometric_id') or '').strip()
        return biometric_id or None


class EmployeeDocumentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = EmployeeDocument
        fields = ['doc_type', 'file', 'note']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class WorkshopForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Workshop
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
