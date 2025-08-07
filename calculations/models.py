from django.conf import settings
from django.db import models

# Create your models here.
class Calculation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_complete = models.BooleanField(default=False)

    organisation_INN = models.CharField(max_length=12)
    organisation_KPP = models.CharField(max_length=9)
    organisation_OGRN = models.CharField(max_length=13)
    organisation_name = models.CharField(max_length=300)
    organisation_address = models.CharField(max_length=300)


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
    value_after = models.CharField(max_length=300)
    actions_description = models.TextField(blank=True)

    class Meta:
        unique_together = ('calculation', 'parameter')
