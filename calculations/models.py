from django.conf import settings
from django.db import models

# Create your models here.
class Organisation(models.Model):
    INN = models.CharField(max_length=12, verbose_name="ИНН")
    KPP = models.CharField(max_length=9, verbose_name="КПП")
    OGRN = models.CharField(max_length=13, verbose_name="ОГРН")
    name = models.CharField(max_length=300, verbose_name="Наименование организации")
    address = models.CharField(max_length=300, verbose_name="Адрес")

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"


class Calculation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_complete = models.BooleanField(default=False)

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="calculations",
        verbose_name="Организация",
        null=True,
        blank=True
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children"
    )

    class Meta:
        verbose_name = "Расчёт"
        verbose_name_plural = "Расчёты"


class ParameterGroup(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=300)


class Parameter(models.Model):
    group = models.ForeignKey(ParameterGroup, on_delete=models.CASCADE, related_name='parameters')
    text = models.TextField()
    order_num = models.PositiveIntegerField()


class ParameterOption(models.Model):
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=300)
    coefficient = models.FloatField()


class CalculationParameterData(models.Model):
    calculation = models.ForeignKey(Calculation, on_delete=models.CASCADE, related_name='parameter_data')
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    
    value_before = models.CharField(max_length=300)
    actions_description = models.TextField(blank=True)

    class Meta:
        unique_together = ('calculation', 'parameter')


class CalculationResult(models.Model):
    calculation = models.ForeignKey(
        Calculation,
        on_delete=models.CASCADE,
        related_name='results'
    )
    group = models.ForeignKey(
        ParameterGroup,
        on_delete=models.CASCADE
    )

    before_sum = models.FloatField(default=0.0)
    before_percentage = models.FloatField(default=0.0)
    before_linguistic_level = models.CharField(max_length=50, default='Не оценивается')

    max_sum = models.FloatField(default=0.0)

    difference = models.FloatField(default=0.0)
    conclusion = models.CharField(max_length=100, default='')

    class Meta:
        unique_together = ('calculation', 'group')
        verbose_name = 'Результат расчета'
        verbose_name_plural = 'Результаты расчетов'


class Industry(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Отрасль промышленности")

    def __str__(self):
        return self.name
    

class DeathStatistic(models.Model):
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE, related_name="death_stats", verbose_name="Отрасль")
    year = models.PositiveIntegerField(verbose_name="Год")
    deaths = models.PositiveIntegerField(verbose_name="Количество погибших")
    workers_in_industry = models.PositiveIntegerField(verbose_name="Количество работников в отрасли")

    class Meta:
        unique_together = ("industry", "year")
        verbose_name = "Смерти за год"

    def __str__(self):
        return f"{self.industry} – {self.year}: {self.deaths}"
    
    
class RiskCalculation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    industry = models.ForeignKey(Industry, on_delete=models.PROTECT, verbose_name="Отрасль")
    year = models.PositiveIntegerField(verbose_name="Год расчёта")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_short_shift = models.BooleanField(default=False, verbose_name="Смены менее 2 часов")
    result = models.FloatField(verbose_name="Результат расчёта")

    class Meta:
        verbose_name = "Расчёт индивидуального риска"

    def __str__(self):
        return f"Расчёт {self.year} – {self.industry}"
