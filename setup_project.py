import os
from pathlib import Path

BASE_DIR = Path(r"c:\Users\gurut\Iseng\PreDish")

def write_file(path, content):
    filepath = BASE_DIR / path
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# DIRS
dirs = [
    'templates/partials',
    'accounts/templates/accounts',
    'business/templates/business/onboarding',
    'sales/templates/sales',
    'forecast/templates/forecast',
    'notifications/templates/notifications',
    'billing/templates/billing',
    'static/css',
]
for d in dirs:
    (BASE_DIR / d).mkdir(parents=True, exist_ok=True)

# 1. predish/settings.py
settings_content = """import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-mvp-secret-key-change-in-production'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'accounts',
    'business',
    'sales',
    'forecast',
    'notifications',
    'billing',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'predish.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'predish.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'id'
TIME_ZONE = 'Asia/Jakarta' 
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
"""
write_file('predish/settings.py', settings_content)

# 2. requirements.txt
req_content = """Django>=5.0,<6.0
pandas>=2.0.0
openpyxl>=3.1.0
"""
write_file('requirements.txt', req_content)

# 3. predish/urls.py
predish_urls_content = """from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def index_view(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    
    try:
        business = request.user.businesses.first()
        if not business or not business.onboarding_done:
            return redirect('business:onboarding_step1')
    except:
        return redirect('business:onboarding_step1')
        
    return redirect('/#dashboard-coming-soon')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index_view, name='index'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('onboarding/', include('business.urls', namespace='business')),
]
"""
write_file('predish/urls.py', predish_urls_content)

# APPS INITIALIZATION (__init__.py, apps.py, admin.py)
apps = ['accounts', 'business', 'sales', 'forecast', 'notifications', 'billing']
for app in apps:
    write_file(f'{app}/__init__.py', '')
    apps_content = f"""from django.apps import AppConfig

class {app.capitalize()}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '{app}'
"""
    write_file(f'{app}/apps.py', apps_content)
    
# BUSINESS MODELS
biz_models_content = """from django.db import models
from django.contrib.auth.models import User

class Business(models.Model):
    TYPE_CHOICES = (
        ('cafe', 'Kafe'),
        ('restaurant', 'Restoran'),
        ('catering', 'Katering'),
    )
    
    PLAN_CHOICES = (
        ('freemium', 'Freemium'),
        ('starter', 'Starter'),
        ('growth', 'Growth'),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='businesses')
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    plan = models.CharField(max_length=50, choices=PLAN_CHOICES, default='freemium')
    onboarding_done = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Businesses"

    def __str__(self):
        return f"{self.name} ({self.owner.username})"

class MenuItem(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['business', 'name']

    def __str__(self):
        return f"{self.name} - {self.business.name}"
"""
write_file('business/models.py', biz_models_content)

# BUSINESS ADMIN
biz_admin_content = """from django.contrib import admin
from .models import Business, MenuItem

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'type', 'plan', 'onboarding_done', 'created_at')
    list_filter = ('type', 'plan', 'onboarding_done')
    search_fields = ('name', 'owner__username')

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'is_active', 'created_at')
    list_filter = ('is_active', 'business')
    search_fields = ('name', 'business__name')
"""
write_file('business/admin.py', biz_admin_content)

# SALES MODELS
sales_models_content = """from django.db import models
from business.models import MenuItem

class DailySale(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='daily_sales')
    date = models.DateField()
    qty_sold = models.PositiveIntegerField()
    qty_produced = models.PositiveIntegerField(null=True, blank=True)
    qty_leftover = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'menu_item__name']
        constraints = [
            models.UniqueConstraint(
                fields=["menu_item", "date"],
                name="unique_menu_sale_per_day"
            )
        ]

    def __str__(self):
        return f"{self.menu_item.name} - {self.date}: {self.qty_sold} sold"
"""
write_file('sales/models.py', sales_models_content)

# SALES ADMIN
sales_admin_content = """from django.contrib import admin
from .models import DailySale

@admin.register(DailySale)
class DailySaleAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'date', 'qty_sold', 'qty_produced', 'qty_leftover')
    list_filter = ('date', 'menu_item__business')
    search_fields = ('menu_item__name',)
"""
write_file('sales/admin.py', sales_admin_content)

# FORECAST MODELS
fc_models_content = """from django.db import models
from business.models import Business, MenuItem

class ExternalFactor(models.Model):
    DAY_TYPE_CHOICES = (
        ('weekday', 'Weekday'),
        ('weekend', 'Weekend'),
        ('holiday', 'Libur Nasional'),
    )
    PERIOD_CHOICES = (
        ('old_date', 'Tanggal Tua'),
        ('payday', 'Tanggal Gajian'),
        ('young_date', 'Tanggal Muda'),
    )
    WEATHER_CHOICES = (
        ('clear', 'Cerah'),
        ('cloudy', 'Berawan'),
        ('rainy', 'Hujan'),
    )

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='external_factors')
    date = models.DateField()
    day_type = models.CharField(max_length=50, choices=DAY_TYPE_CHOICES)
    period = models.CharField(max_length=50, choices=PERIOD_CHOICES)
    weather = models.CharField(max_length=50, choices=WEATHER_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=["business", "date"],
                name="unique_external_factor_per_day"
            )
        ]

    def __str__(self):
        return f"{self.business.name} - {self.date} ({self.get_day_type_display()})"


class Forecast(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='forecasts')
    target_date = models.DateField()
    recommended_qty = models.PositiveIntegerField()
    confidence = models.PositiveIntegerField()
    data_days_used = models.PositiveIntegerField()
    factors_snapshot = models.JSONField(help_text="Snapshot dari faktor dan adjustment saat diprediksi")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-target_date']
        constraints = [
            models.UniqueConstraint(
                fields=["menu_item", "target_date"],
                name="unique_forecast_per_day"
            )
        ]

    def __str__(self):
        return f"Forecast {self.menu_item.name} for {self.target_date}: {self.recommended_qty} qty"
"""
write_file('forecast/models.py', fc_models_content)

# FORECAST ADMIN
fc_admin_content = """from django.contrib import admin
from .models import ExternalFactor, Forecast

@admin.register(ExternalFactor)
class ExternalFactorAdmin(admin.ModelAdmin):
    list_display = ('business', 'date', 'day_type', 'period', 'weather')
    list_filter = ('day_type', 'period', 'weather', 'business')

@admin.register(Forecast)
class ForecastAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'target_date', 'recommended_qty', 'confidence')
    list_filter = ('target_date', 'menu_item__business')
"""
write_file('forecast/admin.py', fc_admin_content)

# NOTIFICATIONS MODELS
notif_models_content = """from django.db import models
from business.models import Business

class NotificationSetting(models.Model):
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name='notification_setting')
    email_daily = models.BooleanField(default=True)
    popup = models.BooleanField(default=True)
    reminder_input_night = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.business.name}"
"""
write_file('notifications/models.py', notif_models_content)

# NOTIFICATIONS ADMIN
notif_admin_content = """from django.contrib import admin
from .models import NotificationSetting

@admin.register(NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    list_display = ('business', 'email_daily', 'popup', 'reminder_input_night')
"""
write_file('notifications/admin.py', notif_admin_content)


# --- TAHAP 2 ---

# ACCOUNTS URLS
acc_urls = """from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='accounts:login'), name='logout'),
]
"""
write_file('accounts/urls.py', acc_urls)

# ACCOUNTS FORMS
acc_forms = """from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email']
"""
write_file('accounts/forms.py', acc_forms)

# ACCOUNTS VIEWS
acc_views = """from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomUserCreationForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registrasi berhasil. Silakan lengkapi data usaha Anda.")
            return redirect('business:onboarding_step1')
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'accounts/register.html', {'form': form})
"""
write_file('accounts/views.py', acc_views)

# BUSINESS URLS
biz_urls = """from django.urls import path
from . import views

app_name = 'business'

urlpatterns = [
    path('step/1/', views.onboarding_step1, name='onboarding_step1'),
    path('step/2/', views.onboarding_step2, name='onboarding_step2'),
    path('step/3/', views.onboarding_step3, name='onboarding_step3'),
]
"""
write_file('business/urls.py', biz_urls)

# BUSINESS FORMS
biz_forms = """from django import forms
from .models import Business

class BusinessProfileForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name', 'type']
        labels = {
            'name': 'Nama Usaha',
            'type': 'Jenis Usaha',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2'}),
            'type': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2'}),
        }
"""
write_file('business/forms.py', biz_forms)

# BUSINESS VIEWS
biz_views = """from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Business, MenuItem
from .forms import BusinessProfileForm

@login_required
def onboarding_step1(request):
    business, created = Business.objects.get_or_create(owner=request.user)
    
    if business.onboarding_done:
        return redirect('/') 
        
    if request.method == 'POST':
        form = BusinessProfileForm(request.POST, instance=business)
        if form.is_valid():
            form.save()
            return redirect('business:onboarding_step2')
    else:
        form = BusinessProfileForm(instance=business)
        
    return render(request, 'business/onboarding/step1.html', {'form': form})

@login_required
def onboarding_step2(request):
    try:
        business = Business.objects.get(owner=request.user)
    except Business.DoesNotExist:
        return redirect('business:onboarding_step1')
        
    if business.onboarding_done:
        return redirect('/')

    if request.method == 'POST':
        return redirect('business:onboarding_step3')

    return render(request, 'business/onboarding/step2.html')

@login_required
def onboarding_step3(request):
    try:
        business = Business.objects.get(owner=request.user)
    except Business.DoesNotExist:
        return redirect('business:onboarding_step1')

    if business.onboarding_done:
        return redirect('/')

    if request.method == 'POST':
        menus = request.POST.getlist('menus')
        menus = [m.strip() for m in menus if m.strip()]
        
        if business.plan == 'freemium' and len(menus) > 2:
            messages.error(request, "Pada paket Freemium, maksimal 2 menu dapat diprediksi.")
            return redirect('business:onboarding_step3')
            
        if not menus:
            messages.error(request, "Pilih atau isi setidaknya 1 menu.")
            return redirect('business:onboarding_step3')

        for menu_name in menus:
            MenuItem.objects.get_or_create(business=business, name=menu_name)
            
        business.onboarding_done = True
        business.save()
        messages.success(request, "Onboarding selesai! Selamat datang di PreDish.")
        return redirect('/') 

    existing_menus = MenuItem.objects.filter(business=business)
    return render(request, 'business/onboarding/step3.html', {
        'business': business,
        'existing_menus': existing_menus
    })
"""
write_file('business/views.py', biz_views)

# TEMPLATES: base.html
base_html = """<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PreDish - Dari Insting ke Data</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: { primary: '#16a34a', }
                }
            }
        }
    </script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-50 text-gray-800 min-h-screen flex flex-col font-sans">
    
    {% include 'partials/navbar.html' %}
    {% include 'partials/messages.html' %}

    <main class="flex-grow container mx-auto px-4 py-8">
        {% block content %}{% endblock %}
    </main>

</body>
</html>
"""
write_file('templates/base.html', base_html)

# TEMPLATES: navbar.html
navbar_html = """<nav class="bg-white shadow-sm border-b border-gray-100">
    <div class="container mx-auto px-4 py-3 flex justify-between items-center">
        <a href="/" class="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <div class="w-8 h-8 rounded bg-primary text-white flex items-center justify-center font-bold">P</div>
            PreDish
        </a>
        <div>
            {% if user.is_authenticated %}
                <span class="mr-4 text-sm text-gray-600">Halo, {{ user.username }}</span>
                <form action="{% url 'accounts:logout' %}" method="POST" class="inline">
                    {% csrf_token %}
                    <button type="submit" class="text-sm font-medium text-red-600 hover:text-red-700">Keluar</button>
                </form>
            {% endif %}
        </div>
    </div>
</nav>
"""
write_file('templates/partials/navbar.html', navbar_html)

# TEMPLATES: messages.html
msgs_html = """{% if messages %}
<div class="container mx-auto px-4 mt-4">
    {% for message in messages %}
        <div class="p-4 rounded mb-2 {% if message.tags == 'error' %}bg-red-100 text-red-700{% elif message.tags == 'warning' %}bg-yellow-100 text-yellow-700{% else %}bg-green-100 text-green-700{% endif %}">
            {{ message }}
        </div>
    {% endfor %}
</div>
{% endif %}
"""
write_file('templates/partials/messages.html', msgs_html)

# TEMPLATES: accounts/login.html
login_html = """{% extends "base.html" %}

{% block content %}
<div class="max-w-md mx-auto bg-white p-8 rounded-xl shadow-sm border border-gray-100 mt-10">
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Masuk ke PreDish</h1>
    <form method="POST">
        {% csrf_token %}
        <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">Username</label>
            <input type="text" name="username" class="w-full border border-gray-300 rounded px-3 py-2 focus:border-primary focus:ring-1 focus:ring-primary outline-none" required>
        </div>
        <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input type="password" name="password" class="w-full border border-gray-300 rounded px-3 py-2 focus:border-primary focus:ring-1 focus:ring-primary outline-none" required>
        </div>
        <button type="submit" class="w-full bg-primary text-white font-medium py-2 rounded hover:bg-green-700 transition">Masuk</button>
    </form>
    <p class="mt-4 text-sm text-center text-gray-600">
        Belum punya akun? <a href="{% url 'accounts:register' %}" class="text-primary hover:underline">Daftar sekarang</a>
    </p>
</div>
{% endblock %}
"""
write_file('accounts/templates/accounts/login.html', login_html)

# TEMPLATES: accounts/register.html
register_html = """{% extends "base.html" %}

{% block content %}
<div class="max-w-md mx-auto bg-white p-8 rounded-xl shadow-sm border border-gray-100 mt-10">
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Daftar Akun Baru</h1>
    <form method="POST">
        {% csrf_token %}
        {% for field in form %}
            <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-1">{{ field.label }}</label>
                {{ field }}
                {% if field.help_text %}
                    <p class="text-xs text-gray-500 mt-1">{{ field.help_text }}</p>
                {% endif %}
                {% for error in field.errors %}
                    <p class="text-xs text-red-500 mt-1">{{ error }}</p>
                {% endfor %}
            </div>
        {% endfor %}
        <button type="submit" class="w-full bg-primary text-white font-medium py-2 rounded hover:bg-green-700 transition mt-2">Daftar</button>
    </form>
    <p class="mt-4 text-sm text-center text-gray-600">
        Sudah punya akun? <a href="{% url 'accounts:login' %}" class="text-primary hover:underline">Masuk</a>
    </p>
</div>
{% endblock %}
"""
write_file('accounts/templates/accounts/register.html', register_html)

# TEMPLATES: business/onboarding/step1.html
s1_html = """{% extends "base.html" %}

{% block content %}
<div class="max-w-xl mx-auto bg-white p-8 rounded-xl shadow-sm border border-gray-100 mt-10">
    <div class="text-sm font-medium text-gray-500 mb-2">Langkah 1 dari 3</div>
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Profil Usaha</h1>
    <form method="POST">
        {% csrf_token %}
        {{ form.as_p }}
        <div class="mt-6 flex justify-end">
            <button type="submit" class="bg-primary text-white font-medium px-6 py-2 rounded hover:bg-green-700 transition">Selanjutnya</button>
        </div>
    </form>
</div>
{% endblock %}
"""
write_file('business/templates/business/onboarding/step1.html', s1_html)

# TEMPLATES: business/onboarding/step2.html
s2_html = """{% extends "base.html" %}

{% block content %}
<div class="max-w-2xl mx-auto bg-white p-8 rounded-xl shadow-sm border border-gray-100 mt-10">
    <div class="text-sm font-medium text-gray-500 mb-2">Langkah 2 dari 3</div>
    <h1 class="text-2xl font-bold text-gray-800 mb-2">Bagaimana Anda akan memasukkan data?</h1>
    <p class="text-gray-600 mb-6">Anda bisa mengganti metode ini kapan saja nantinya.</p>

    <form method="POST">
        {% csrf_token %}
        <div class="grid md:grid-cols-2 gap-4 mb-8">
            <label class="border rounded-lg p-6 flex flex-col items-center cursor-pointer hover:border-primary hover:bg-green-50 transition border-primary bg-green-50">
                <input type="radio" name="input_method" value="manual" checked class="hidden">
                <span class="text-lg font-bold text-gray-800 mb-2">Input Manual</span>
                <span class="text-sm text-gray-500 text-center">Saya akan memasukkan penjualan setiap hari melalui aplikasi.</span>
            </label>
            
            <label class="border rounded-lg p-6 flex flex-col items-center cursor-pointer hover:border-primary hover:bg-green-50 transition opacity-70">
                <input type="radio" name="input_method" value="upload" class="hidden">
                <span class="text-lg font-bold text-gray-800 mb-2">Upload File Excel/CSV</span>
                <span class="text-sm text-gray-500 text-center">Saya sudah punya rekap data dan akan mengunggahnya nanti.</span>
            </label>
        </div>

        <div class="flex justify-between">
            <a href="{% url 'business:onboarding_step1' %}" class="text-gray-600 font-medium px-6 py-2 hover:bg-gray-100 rounded">Kembali</a>
            <button type="submit" class="bg-primary text-white font-medium px-6 py-2 rounded hover:bg-green-700 transition">Selanjutnya</button>
        </div>
    </form>
</div>
{% endblock %}
"""
write_file('business/templates/business/onboarding/step2.html', s2_html)

# TEMPLATES: business/onboarding/step3.html
s3_html = """{% extends "base.html" %}

{% block content %}
<div class="max-w-2xl mx-auto bg-white p-8 rounded-xl shadow-sm border border-gray-100 mt-10">
    <div class="text-sm font-medium text-gray-500 mb-2">Langkah 3 dari 3</div>
    <h1 class="text-2xl font-bold text-gray-800 mb-2">Pilih Menu</h1>
    <p class="text-gray-600 mb-6">Tuliskan nama menu utama yang ingin diprediksi penjualannya.</p>
    
    {% if business.plan == 'freemium' %}
    <div class="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded mb-6 text-sm">
        Anda berada di paket <strong>Freemium</strong>. Anda maksimal dapat memprediksi <strong>2 menu</strong>.
    </div>
    {% endif %}

    <form method="POST">
        {% csrf_token %}
        <div class="space-y-3 mb-8" id="menu-container">
            <input type="text" name="menus" placeholder="Contoh: Nasi Goreng Spesial" class="w-full border border-gray-300 rounded px-3 py-2" {% if business.plan == 'freemium' %}required{% endif %}>
            <input type="text" name="menus" placeholder="Contoh: Ayam Geprek" class="w-full border border-gray-300 rounded px-3 py-2">
        </div>
        
        {% if business.plan != 'freemium' %}
        <button type="button" onclick="addMenuInput()" class="text-sm text-primary font-medium hover:underline mb-6">+ Tambah baris menu</button>
        {% endif %}

        <div class="flex justify-between">
            <a href="{% url 'business:onboarding_step2' %}" class="text-gray-600 font-medium px-6 py-2 hover:bg-gray-100 rounded">Kembali</a>
            <button type="submit" class="bg-primary text-white font-medium px-6 py-2 rounded hover:bg-green-700 transition">Selesai & Mulai</button>
        </div>
    </form>
</div>

<script>
    function addMenuInput() {
        const container = document.getElementById('menu-container');
        const input = document.createElement('input');
        input.type = 'text';
        input.name = 'menus';
        input.placeholder = 'Nama menu lainnya...';
        input.className = 'w-full border border-gray-300 rounded px-3 py-2 mt-3';
        container.appendChild(input);
    }
</script>
{% endblock %}
"""
write_file('business/templates/business/onboarding/step3.html', s3_html)
