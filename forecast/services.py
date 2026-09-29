import statistics
from datetime import timedelta
from django.db.models import Sum
from sales.models import DailySale
from .models import Forecast, ExternalFactor

FORECAST_FACTORS = {
    "weekday": 1.0,
    "weekend": 1.05,
    "holiday": 1.10,
    "old_date": 0.94,
    "payday": 1.08,
    "young_date": 0.97,
    "rainy": 0.90,
    "cloudy": 0.98,
    "clear": 1.0,
}

def is_weekend(date_obj):
    # Monday = 0, Sunday = 6
    return date_obj.weekday() >= 5

def calculate_forecast(menu_item, target_date, external_factor=None):
    """
    1. Mengambil data penjualan historis (maksimal 14 hari)
    2. Memisahkan baseline hari (weekday/weekend) jika cukup
    3. WMA / Simple Average
    4. Faktor eksternal
    5. Confidence
    """
    end_date = target_date - timedelta(days=1)
    
    # 1. Ambil data historis
    past_sales = DailySale.objects.filter(
        menu_item=menu_item, 
        date__lte=end_date
    ).order_by('-date')
    
    target_day_type = external_factor.day_type if external_factor else ('weekend' if is_weekend(target_date) else 'weekday')
    target_is_weekend = (target_day_type in ['weekend', 'holiday'])
    
    # 2. Pisahkan baseline
    matched_sales = []
    for sale in past_sales:
        if len(matched_sales) >= 14:
            break
        if is_weekend(sale.date) == target_is_weekend:
            matched_sales.append(sale)
            
    # Jika data tidak cukup (< 7), fallback ke seluruh data historis
    if len(matched_sales) < 7:
        matched_sales = list(past_sales[:14])
        
    data_days_used = len(matched_sales)
    
    # Cold start (tidak ada data)
    if data_days_used == 0:
        return _save_forecast(menu_item, target_date, 0, 0, 0, external_factor)

    # 3. Hitung WMA atau Simple Average
    if data_days_used < 7:
        # Simple average
        total_qty = sum(s.qty_sold for s in matched_sales)
        baseline = total_qty / data_days_used
    else:
        # Weighted Moving Average
        total_weight = 0
        weighted_sum = 0
        # matched_sales diurutkan dari yang terbaru, jadi matched_sales[0] mendapat bobot paling besar
        for i, sale in enumerate(matched_sales):
            weight = data_days_used - i
            weighted_sum += sale.qty_sold * weight
            total_weight += weight
        baseline = weighted_sum / total_weight

    # 4. Faktor eksternal
    adj_day, adj_period, adj_weather = 1.0, 1.0, 1.0
    if external_factor:
        adj_day = FORECAST_FACTORS.get(external_factor.day_type, 1.0)
        adj_period = FORECAST_FACTORS.get(external_factor.period, 1.0)
        adj_weather = FORECAST_FACTORS.get(external_factor.weather, 1.0)
        
    final_forecast = baseline * adj_day * adj_period * adj_weather
    
    recommended_qty = int(round(final_forecast))
    if recommended_qty < 0:
        recommended_qty = 0

    # 5. Hitung Confidence (0-100)
    base_conf = (data_days_used / 14.0) * 100
    variation_penalty = 0
    if data_days_used > 1:
        qtys = [s.qty_sold for s in matched_sales]
        mean_qty = statistics.mean(qtys)
        if mean_qty > 0:
            cv = statistics.stdev(qtys) / mean_qty
            variation_penalty = min(cv * 30, 30) # Penalti max 30% untuk variasi tinggi
            
    confidence = int(max(0, min(100, base_conf - variation_penalty)))
    
    # Warning penalty jika data kurang dari 7 hari
    if data_days_used < 7:
        confidence = min(confidence, 50)
        
    return _save_forecast(menu_item, target_date, recommended_qty, confidence, data_days_used, external_factor, adj_day, adj_period, adj_weather)

def _save_forecast(menu, target_date, qty, conf, days_used, ext_factor, adj_d=1.0, adj_p=1.0, adj_w=1.0):
    factors_snapshot = {}
    if ext_factor:
        factors_snapshot = {
            "day_type": ext_factor.day_type,
            "period": ext_factor.period,
            "weather": ext_factor.weather,
            "adjustments": {
                "day": adj_d,
                "period": adj_p,
                "weather": adj_w
            }
        }
    
    forecast, _ = Forecast.objects.update_or_create(
        menu_item=menu,
        target_date=target_date,
        defaults={
            'recommended_qty': qty,
            'confidence': conf,
            'data_days_used': days_used,
            'factors_snapshot': factors_snapshot
        }
    )
    return forecast

def calculate_accuracy(prediction, actual):
    """
    Hitung akurasi dalam persen.
    Jika actual == 0, fallback: 
    Jika prediction == 0 -> 100%
    Jika prediction > 0  -> 0%
    """
    if actual == 0:
        return 100.0 if prediction == 0 else 0.0
        
    acc = 1 - abs(prediction - actual) / actual
    return max(0.0, acc * 100)
