from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Business, MenuItem

@login_required
def onboarding_step1(request):
    business = request.user.businesses.first()
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            if business:
                business.name = name
                business.save()
            else:
                Business.objects.create(owner=request.user, name=name)
            return redirect('business:onboarding_step2')
    return render(request, 'business/step1_profile.html', {'business': business})

@login_required
def onboarding_step2(request):
    business = request.user.businesses.first()
    if not business:
        return redirect('business:onboarding_step1')
        
    if request.method == 'POST':
        business_type = request.POST.get('type')
        if business_type:
            business.type = business_type
            business.save()
            return redirect('business:onboarding_step3')
            
    return render(request, 'business/step2_type.html', {'business': business})

@login_required
def onboarding_step3(request):
    business = request.user.businesses.first()
    if not business:
        return redirect('business:onboarding_step1')
        
    if request.method == 'POST':
        menus = request.POST.getlist('menus[]')
        for menu_name in menus:
            if menu_name.strip():
                MenuItem.objects.get_or_create(business=business, name=menu_name.strip())
        
        business.onboarding_done = True
        business.save()
        return redirect('sales:input_data')
        
    return render(request, 'business/step3_menus.html')

@login_required
def manage_menus(request):
    business = request.user.businesses.first()
    if not business:
        return redirect('business:onboarding_step1')
        
    if request.method == 'POST':
        menu_name = request.POST.get('menu_name')
        if menu_name:
            menu, created = MenuItem.objects.get_or_create(business=business, name=menu_name.strip(), defaults={'is_active': True})
            if not created and not menu.is_active:
                menu.is_active = True
                menu.save()
            messages.success(request, f"Menu '{menu_name}' berhasil ditambahkan.")
        return redirect('business:manage_menus')
        
    # Only show active menus
    menus = MenuItem.objects.filter(business=business, is_active=True).order_by('name')
    return render(request, 'business/manage_menus.html', {'menus': menus})

@login_required
def delete_menu(request, menu_id):
    business = request.user.businesses.first()
    if not business:
        return redirect('business:onboarding_step1')
        
    if request.method == 'POST':
        menu = MenuItem.objects.filter(id=menu_id, business=business).first()
        if menu:
            # We perform a "soft delete" by setting is_active = False.
            # This is crucial so that we don't accidentally delete past sales records
            # that refer to this menu item.
            menu.is_active = False
            menu.save()
            messages.success(request, f"Menu '{menu.name}' berhasil dihapus.")
            
    return redirect('business:manage_menus')
