import json
from datetime import date, timedelta
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from business.models import MenuItem
from sales.models import DailySale
from .models import ExternalFactor, Forecast
from .services import calculate_forecast

@login_required
def variables(request):
    business = request.user.businesses.first()
    target_date = date.today() + timedelta(days=1)
    
    if request.method == 'POST':
        day_type = request.POST.get('day_type')
        period = request.POST.get('period')
        weather = request.POST.get('weather')
        
        ExternalFactor.objects.update_or_create(
            business=business, date=target_date,
            defaults={'day_type': day_type, 'period': period, 'weather': weather}
        )
        return redirect('forecast:calculate')
        
    return render(request, 'forecast/variables.html', {'target_date': target_date})

@login_required
def calculate_view(request):
    business = request.user.businesses.first()
    target_date = date.today() + timedelta(days=1)
    
    factor = ExternalFactor.objects.filter(business=business, date=target_date).first()
    menus = MenuItem.objects.filter(business=business, is_active=True)
    
    for menu in menus:
        calculate_forecast(menu, target_date, factor)
        
    messages.success(request, "Rekomendasi berhasil diperbarui.")
    return redirect('forecast:dashboard')

@login_required
def dashboard(request):
    business = request.user.businesses.first()
    target_date = date.today() + timedelta(days=1)
    yesterday = date.today() - timedelta(days=1)
    
    forecasts = Forecast.objects.filter(menu_item__business=business, target_date=target_date, menu_item__is_active=True)
    factor = ExternalFactor.objects.filter(business=business, date=target_date).first()
    
    avg_confidence = sum(f.confidence for f in forecasts) / forecasts.count() if forecasts.exists() else 0
        
    forecast_data = []
    for f in forecasts:
        last_sale = DailySale.objects.filter(menu_item=f.menu_item).order_by('-date').first()
        diff = (f.recommended_qty - last_sale.qty_sold) if last_sale else 0
        forecast_data.append({'menu_name': f.menu_item.name, 'qty': f.recommended_qty, 'diff': diff, 'id': f.id})
        
    # Chart data historis dari data pertama hingga besok (prediksi)
    first_sale = DailySale.objects.filter(menu_item__business=business).order_by('date').first()
    if first_sale:
        start_date = first_sale.date
        # Batasi maksimal 30 hari agar grafik tidak terlalu padat di masa depan
        if (target_date - start_date).days > 30:
            start_date = target_date - timedelta(days=30)
    else:
        start_date = target_date - timedelta(days=7)
        
    delta_days = (target_date - start_date).days
    
    labels, actuals, predictions = [], [], []
    for i in range(delta_days, -1, -1):
        d = target_date - timedelta(days=i)
        labels.append(d.strftime("%d %b"))
        
        act_query = DailySale.objects.filter(menu_item__business=business, date=d, menu_item__is_active=True).aggregate(Sum('qty_sold'))['qty_sold__sum']
        act = act_query if act_query is not None else None
        actuals.append(act)
        
        prd_query = Forecast.objects.filter(menu_item__business=business, target_date=d, menu_item__is_active=True).aggregate(Sum('recommended_qty'))['recommended_qty__sum']
        prd = prd_query if prd_query is not None else None
        predictions.append(prd)
        
    chart_json = json.dumps({
        'labels': labels,
        'datasets': [
            {'label': 'Aktual', 'data': actuals, 'borderColor': '#16a34a', 'fill': False},
            {'label': 'Prediksi', 'data': predictions, 'borderColor': '#eab308', 'fill': False, 'borderDash': [5, 5]}
        ]
    })
    
    return render(request, 'forecast/dashboard.html', {
        'target_date': target_date, 'factor': factor, 'forecast_data': forecast_data,
        'avg_confidence': int(avg_confidence), 'chart_json': chart_json
    })

@login_required
def apply_action(request):
    if request.method == 'POST':
        business = request.user.businesses.first()
        target_date = date.today() + timedelta(days=1)
        forecasts = Forecast.objects.filter(menu_item__business=business, target_date=target_date)
        
        for f in forecasts:
            manual_qty = request.POST.get(f'qty_{f.id}')
            qty_to_produce = int(manual_qty) if manual_qty else f.recommended_qty
            DailySale.objects.update_or_create(
                menu_item=f.menu_item, date=target_date,
                defaults={'qty_produced': qty_to_produce}
            )
        messages.success(request, "Rencana produksi besok berhasil diterapkan.")
    return redirect('forecast:dashboard')
