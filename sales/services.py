import pandas as pd
from django.db import transaction
from django.utils.dateparse import parse_date
from business.models import MenuItem
from .models import DailySale

def process_sales_upload(file_obj, business):
    errors = []
    success_count = 0
    total_rows = 0
    
    try:
        if file_obj.name.endswith('.csv'):
            df = pd.read_csv(file_obj)
        elif file_obj.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_obj)
        else:
            return 0, 0, ["Format file tidak didukung. Harap gunakan file Excel (.xlsx / .xls)."]
    except Exception as e:
        return 0, 0, [f"Gagal membaca file: {str(e)}"]
        
    df.columns = [str(c).lower().strip() for c in df.columns]
        
    required_cols = ['tanggal', 'menu', 'terjual', 'sisa']
    for col in required_cols:
        if col not in df.columns:
            return 0, 0, [f"Kolom wajib '{col}' tidak ditemukan dalam file."]

    total_rows = len(df)
    
    with transaction.atomic():
        for index, row in df.iterrows():
            row_num = index + 2
            
            tanggal_str = str(row['tanggal']).strip()
            menu_name = str(row['menu']).strip()
            
            if pd.isna(row['tanggal']) or not tanggal_str or tanggal_str.lower() == 'nan':
                errors.append(f"Baris {row_num}: Tanggal kosong.")
                continue
                
            if pd.isna(row['menu']) or not menu_name or menu_name.lower() == 'nan':
                errors.append(f"Baris {row_num}: Nama menu kosong.")
                continue
                
            try:
                date_obj = pd.to_datetime(tanggal_str).date()
            except:
                errors.append(f"Baris {row_num}: Format tanggal tidak valid ({tanggal_str}).")
                continue
                
            try:
                qty_sold = int(float(str(row['terjual']).strip()))
                qty_left = int(float(str(row['sisa']).strip()))
                if qty_sold < 0 or qty_left < 0:
                    raise ValueError
            except:
                errors.append(f"Baris {row_num}: 'Terjual' dan 'Sisa' harus berupa angka positif.")
                continue
            
            menu_item, created = MenuItem.objects.get_or_create(
                business=business, 
                name=menu_name,
                defaults={'is_active': True}
            )
            if not created and not menu_item.is_active:
                menu_item.is_active = True
                menu_item.save()
            
            qty_produced = qty_sold + qty_left

            DailySale.objects.update_or_create(
                menu_item=menu_item,
                date=date_obj,
                defaults={'qty_sold': qty_sold, 'qty_produced': qty_produced}
            )
            success_count += 1

    return total_rows, success_count, errors

def get_data_completeness(business):
    total_menus = MenuItem.objects.filter(business=business).count()
    if total_menus == 0:
        return {'total_days': 0, 'total_menus': 0, 'percentage': 0}
        
    total_sales = DailySale.objects.filter(menu_item__business=business).count()
    unique_days = DailySale.objects.filter(menu_item__business=business).values('date').distinct().count()
    
    expected_records = 30 * total_menus
    percentage = min(int((total_sales / expected_records) * 100) if expected_records > 0 else 0, 100)
    
    return {
        'total_days': unique_days,
        'total_menus': total_menus,
        'percentage': percentage
    }
