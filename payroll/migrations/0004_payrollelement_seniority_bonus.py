from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0003_alter_payrollelement_overtime_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='payrollelement',
            name='seniority_bonus',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Prime d'ancienneté"),
        ),
    ]