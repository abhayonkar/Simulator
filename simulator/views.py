from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Run
import json

def index(request):
    """Main dashboard for gas pipeline simulator"""
    return render(request, 'simulator/index.html', {
        'title': 'Gas Pipeline Simulator',
        'total_runs': Run.objects.count()
    })

@csrf_exempt
def start_simulation(request):
    """Start a new simulation run"""
    if request.method == 'POST':
        # Create a new run record
        run = Run.objects.create(path='/tmp/sim_run')
        return JsonResponse({
            'status': 'success',
            'run_id': run.id,
            'message': 'Simulation started successfully'
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def simulation_status(request):
    """Get simulation status"""
    return JsonResponse({
        'status': 'running',
        'total_runs': Run.objects.count(),
        'message': 'Gas Pipeline Simulator is operational'
    })