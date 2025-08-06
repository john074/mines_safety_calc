from django.urls import path
from . import views

app_name = 'calculations'

urlpatterns = [
    path('newcalc/', views.newcalc_view, name='newcalc'),
    path('company/', views.company_view, name='company'),
    path('history/', views.history_view, name='history'),
    path('r0/', views.r0_view, name='r0'),
    path('calc/<int:pk>/', views.calc_details_view, name='calc_details'),
]