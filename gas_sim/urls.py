from django.contrib import admin
from django.urls import path, include
from simulator import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('api/start/', views.start_simulation, name='start_simulation'),
    path('api/status/', views.simulation_status, name='simulation_status'),
]
