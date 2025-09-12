from django.contrib import admin
from django.urls import path, include
from simulator import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    
    # Legacy API endpoints (compatibility)
    path('api/start/', views.start_simulation, name='start_simulation'),
    path('api/status/', views.simulation_status, name='simulation_status'),
    
    # New comprehensive API endpoints
    path('api/network/load/', views.load_gaslib_network, name='load_gaslib_network'),
    path('api/simulation/start/', views.start_simulation, name='start_simulation_new'),
    path('api/simulation/stop/', views.stop_simulation, name='stop_simulation'),
    path('api/simulation/status/', views.simulation_status, name='simulation_status_new'),
    path('api/network/<int:network_id>/', views.network_data, name='network_data'),
    path('api/simulation/<int:simulation_id>/data/', views.simulation_data, name='simulation_data'),
    path('api/alarms/', views.alarms_list, name='alarms_list'),
    path('api/alarms/<int:alarm_id>/acknowledge/', views.acknowledge_alarm, name='acknowledge_alarm'),
    path('api/plcs/status/', views.plc_status, name='plc_status'),
    path('api/sensors/readings/', views.sensor_readings, name='sensor_readings'),
]