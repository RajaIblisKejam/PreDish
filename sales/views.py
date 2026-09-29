import openpyxl
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from business.models import Business, MenuItem
from .models import DailySale
from .services import process_sales_upload, get_data_completeness
from datetime import date, timedelta
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator
from forecast.models import Forecast
from forecast.services import calculate_accuracy

@login_required
def input_data(request):
    business = request.user.businesses.first()
    if not business:
        return redirect('business:onboarding_step1')
        
    menus = MenuItem.objects.filter(business=business, is_active=True)
    completeness = get_data_completeness(business)
    
    if request.method == 'POST':
        if 'upload_file' in request.FILES:
            file_obj = request.FILES['upload_file']
            
            if file_obj.size > 5 * 1024 * 1024:
                messages.error(request, "Ukuran file maksimal 5MB.")
                return redirect('sales:input_data')
                
            total, success, errors = process_sales_upload(file_obj, business)
            
            if success > 0:
                messages.success(request, f"{success} data berhasil disimpan.")
            
            if errors:
                return render(request, 'sales/upload_result.html', {
                    'total': total,
                    'success': success,
                    'errors': errors
                })
            
            return redirect('sales:input_data')
            
        else:
            input_date = request.POST.get('date') or date.today().isoformat()
            saved = 0
            for menu in menus:
                qty_sold_str = request.POST.get(f'qty_{menu.id}')
                qty_left_str = request.POST.get(f'sisa_{menu.id}')
                if qty_sold_str:
                    try:
                        qty_sold = int(qty_sold_str)
                        qty_left = int(qty_left_str) if qty_left_str else 0
                        qty_produced = qty_sold + qty_left
                        
                        DailySale.objects.update_or_create(
                            menu_item=menu, date=parse_date(input_date),
                            defaults={'qty_sold': qty_sold, 'qty_produced': qty_produced}
                        )
                        saved += 1
                    except ValueError:
                        messages.error(request, f"Input tidak valid untuk menu {menu.name}")
            
            if saved > 0:
                messages.success(request, f"Berhasil menyimpan {saved} data penjualan manual.")
            return redirect('sales:input_data')

    return render(request, 'sales/input_data.html', {'menus': menus, 'today': date.today().isoformat(), 'completeness': completeness})

@login_required
def download_template(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Template Penjualan"
    ws.append(['Tanggal', 'Menu', 'Terjual', 'Sisa'])
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="template_penjualan.xlsx"'
    wb.save(response)
    return response

@login_required
def history(request):
    business = request.user.businesses.first()
    sales = DailySale.objects.filter(menu_item__business=business).order_by('-date')
    
    if request.GET.get('start'): sales = sales.filter(date__gte=request.GET.get('start'))
    if request.GET.get('end'): sales = sales.filter(date__lte=request.GET.get('end'))
    if request.GET.get('menu'): sales = sales.filter(menu_item_id=request.GET.get('menu'))
    
    week_ago = date.today() - timedelta(days=7)
    total_acc, valid_acc_count, potensi_overproduction, hemat_hpp = 0, 0, 0, 0
    history_data = []
    
    for s in sales:
        f = Forecast.objects.filter(menu_item=s.menu_item, target_date=s.date).first()
        rec = f.recommended_qty if f else None
        
        if rec is not None and s.qty_sold is not None:
            acc = calculate_accuracy(rec, s.qty_sold)
            if s.date >= week_ago:
                total_acc += acc
                valid_acc_count += 1
                
        left = (s.qty_produced - s.qty_sold) if s.qty_produced and s.qty_sold else 0
                
        if rec is not None and s.qty_produced is not None and rec < s.qty_produced:
            potensi_overproduction += (s.qty_produced - rec)
            hemat_hpp += (s.qty_produced - rec) * 15000 
            
        prod = s.qty_produced or 0
        sold = s.qty_sold or 0
        pct = f"{int((sold / prod) * 100)}%" if prod > 0 else "0%"
                
        history_data.append({
            'id': s.id, 'date': s.date, 'menu': s.menu_item.name, 'prod': prod, 'sold': sold,
            'left': left, 'pct': pct
        })
        
    avg_week_acc = int(total_acc / valid_acc_count) if valid_acc_count > 0 else 0
    paginator = Paginator(history_data, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'sales/history.html', {
        'page_obj': page_obj, 'menus': MenuItem.objects.filter(business=business),
        'avg_week_acc': avg_week_acc, 'hemat_hpp': f"Rp{hemat_hpp:,.0f}".replace(',', '.'), 'potensi_overproduction': potensi_overproduction
    })

@login_required
def history_export(request):
    business = request.user.businesses.first()
    sales = DailySale.objects.filter(menu_item__business=business).order_by('-date')
    if request.GET.get('start'): sales = sales.filter(date__gte=request.GET.get('start'))
    if request.GET.get('end'): sales = sales.filter(date__lte=request.GET.get('end'))
    if request.GET.get('menu'): sales = sales.filter(menu_item_id=request.GET.get('menu'))
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Riwayat Penjualan"
    ws.append(['Tanggal', 'Menu', 'Diproduksi', 'Terjual', 'Sisa', 'Persentase Terjual'])
    
    for s in sales:
        prod = s.qty_produced or 0
        sold = s.qty_sold or 0
        left = prod - sold if prod >= sold else 0
        pct_str = f"{int((sold / prod) * 100)}%" if prod > 0 else "0%"
        
        date_str = s.date.strftime("%Y-%m-%d")
        ws.append([date_str, s.menu_item.name, prod, sold, left, pct_str])
        
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="riwayat_predish.xlsx"'
    wb.save(response)
    return response

@login_required
def edit_sale(request, sale_id):
    business = request.user.businesses.first()
    sale = DailySale.objects.filter(id=sale_id, menu_item__business=business).first()
    if not sale:
        return redirect('sales:history')
        
    sisa = (sale.qty_produced - sale.qty_sold) if sale.qty_produced is not None and sale.qty_sold is not None else 0
        
    if request.method == 'POST':
        qty_sold_str = request.POST.get('terjual')
        qty_left_str = request.POST.get('sisa')
        
        try:
            qty_sold = int(qty_sold_str)
            qty_left = int(qty_left_str) if qty_left_str else 0
            sale.qty_sold = qty_sold
            sale.qty_produced = qty_sold + qty_left
            sale.save()
            messages.success(request, f"Data {sale.menu_item.name} berhasil diperbarui.")
            return redirect('sales:history')
        except ValueError:
            messages.error(request, "Input tidak valid. Pastikan Anda memasukkan angka.")
            
    return render(request, 'sales/edit_sale.html', {'sale': sale, 'sisa': sisa})

@login_required
def delete_sale(request, sale_id):
    business = request.user.businesses.first()
    if request.method == 'POST':
        sale = DailySale.objects.filter(id=sale_id, menu_item__business=business).first()
        if sale:
            date_str = sale.date.strftime('%d %b')
            menu_name = sale.menu_item.name
            sale.delete()
            messages.success(request, f"Data penjualan {menu_name} tanggal {date_str} berhasil dihapus.")
    return redirect('sales:history')
