from django.urls import path
from . import views

app_name = 'calculations'

urlpatterns = [
    path('newcalc/', views.newcalc_view, name='newcalc'),
    path('company/', views.company_view, name='company'),
    path('history/', views.history_view, name='history'),
    path('rX/<int:calc_id>/<str:group_code>/', views.rX_view, name='rX'),
    path('calc/<int:pk>/', views.calc_details_view, name='calc_details'),
    path("save_param_value/", views.save_param_value, name="save_param_value"),
]