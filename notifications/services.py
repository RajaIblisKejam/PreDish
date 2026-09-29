from datetime import date, timedelta
from django.utils import timezone
from sales.models import DailySale
from forecast.models import Forecast
from forecast.services import calculate_accuracy
from .models import Notification

def check_and_create_alerts(business):
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # 1. Peringatan belum input data
    has_yesterday = DailySale.objects.filter(menu_item__business=business, date=yesterday).exists()
    if not has_yesterday:
        Notification.objects.get_or_create(
            business=business, 
            type='missing_data',
            defaults={
                'message': f"Data penjualan tanggal {yesterday.strftime('%d %b')} belum diinput. Segera lengkapi agar prediksi tetap akurat.",
                'created_at': timezone.now()
            }
        )
    else:
        # Jika data sudah diinput, hapus notifikasinya
        Notification.objects.filter(business=business, type='missing_data').delete()
        
    # Evaluasi data kemarin untuk akurasi dan overproduksi
    sales_yesterday = DailySale.objects.filter(menu_item__business=business, date=yesterday)
    total_acc, count = 0, 0
    total_produced, total_sold = 0, 0
    
    for s in sales_yesterday:
        if s.qty_produced is not None: total_produced += s.qty_produced
        if s.qty_sold is not None: total_sold += s.qty_sold
        
        f = Forecast.objects.filter(menu_item=s.menu_item, target_date=s.date).first()
        if f and f.recommended_qty is not None and s.qty_sold is not None:
            total_acc += calculate_accuracy(f.recommended_qty, s.qty_sold)
            count += 1
            
    # 2. Peringatan akurasi drop < 70%
    if count > 0 and (total_acc / count) < 70:
        Notification.objects.get_or_create(
            business=business, 
            type='accuracy_drop',
            defaults={
                'message': f"Akurasi prediksi kemarin turun ke {int(total_acc/count)}%. Pastikan variabel eksternal (cuaca dll) diset dengan benar.",
                'created_at': timezone.now()
            }
        )
    else:
        # Jika akurasi sudah naik di atas 70% (misal karena data diperbaiki), hapus notifikasi
        Notification.objects.filter(business=business, type='accuracy_drop').delete()

    # 3. Peringatan overproduksi ekstrim
    if total_produced > 0:
        leftover = total_produced - total_sold
        if leftover > 0 and (leftover / total_produced) > 0.2:
            Notification.objects.get_or_create(
                business=business, 
                type='overproduction',
                defaults={
                    'message': f"Terdapat sisa produksi cukup tinggi kemarin ({leftover} porsi). Coba pertimbangkan batas rekomendasi hari ini.",
                    'created_at': timezone.now()
                }
            )
        else:
            # Jika sisa produksi normal/sudah teratasi, hapus notifikasi
            Notification.objects.filter(business=business, type='overproduction').delete()
    else:
        Notification.objects.filter(business=business, type='overproduction').delete()
