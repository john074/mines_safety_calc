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
