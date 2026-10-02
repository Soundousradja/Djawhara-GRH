from django.db import migrations, models


def populate_matricules(apps, schema_editor):
    Employee = apps.get_model('employees', 'Employee')
    for employee in Employee.objects.filter(matricule='').iterator():
        employee.matricule = f'DJ{employee.pk:06d}'
        employee.save(update_fields=['matricule'])


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0003_employee_sex'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='matricule',
            field=models.CharField(blank=True, editable=False, max_length=20, verbose_name='Matricule'),
        ),
        migrations.RunPython(populate_matricules, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='employee',
            name='matricule',
            field=models.CharField(blank=True, editable=False, max_length=20, unique=True, verbose_name='Matricule'),
        ),
    ]
