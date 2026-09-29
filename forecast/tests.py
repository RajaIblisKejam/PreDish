from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date, timedelta
from business.models import Business, MenuItem
from sales.models import DailySale
from .models import ExternalFactor
from .services import calculate_forecast, calculate_accuracy

class ForecastServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.business = Business.objects.create(owner=self.user, name="Kopi Senja Cafe", type="cafe")
        self.menu = MenuItem.objects.create(business=self.business, name="Kopi Susu")
        self.target_date = date(2026, 9, 30)
        
    def test_cold_start(self):
        # Tanpa data historis
        forecast = calculate_forecast(self.menu, self.target_date)
        self.assertEqual(forecast.recommended_qty, 0)
        self.assertEqual(forecast.confidence, 0)
        self.assertEqual(forecast.data_days_used, 0)
        
    def test_weighted_moving_average(self):
        # Buat 7 data penjualan berurutan (fallback threshold terpenuhi)
        base_date = self.target_date - timedelta(days=7)
        for i in range(7):
            DailySale.objects.create(
                menu_item=self.menu,
                date=base_date + timedelta(days=i),
                qty_sold=10 + i # Hari terbaru lebih besar (16)
            )
        
        forecast = calculate_forecast(self.menu, self.target_date)
        self.assertGreater(forecast.data_days_used, 0)
        # Karena WMA, bobot terbaru (16) lebih tinggi dibanding yang tertua (10)
        # Simple average = 13, WMA pasti > 13
        self.assertGreater(forecast.recommended_qty, 13)

    def test_weekday_baseline(self):
        # Jika target_date adalah weekday, ia memprioritaskan data weekday.
        target_is_weekday_date = date(2026, 9, 30) # Rabu
        
        # Buat 14 data weekday dgn qty 100, dan 14 data weekend dgn qty 50
        base_date = target_is_weekday_date - timedelta(days=60)
        for i in range(60):
            d = base_date + timedelta(days=i)
            if d.weekday() < 5:
                DailySale.objects.create(menu_item=self.menu, date=d, qty_sold=100)
            else:
                DailySale.objects.create(menu_item=self.menu, date=d, qty_sold=50)
                
        forecast = calculate_forecast(self.menu, target_is_weekday_date)
        # Karena baseline terpisah, WMA akan fokus pada weekday yang bernilai 100
        self.assertEqual(forecast.recommended_qty, 100)
        
    def test_external_factor_adjustment(self):
        # Buat data dummy
        DailySale.objects.create(menu_item=self.menu, date=self.target_date - timedelta(days=1), qty_sold=100)
        
        # rainy = 0.90, young_date = 0.97
        factor = ExternalFactor.objects.create(
            business=self.business,
            date=self.target_date,
            day_type='weekday',
            period='young_date',
            weather='rainy'
        )
        
        forecast = calculate_forecast(self.menu, self.target_date, factor)
        expected = int(round(100 * 1.0 * 0.97 * 0.90))
        self.assertEqual(forecast.recommended_qty, expected)
        
    def test_confidence(self):
        # Kurang dari 7 hari harus penalty di bawah 50
        DailySale.objects.create(menu_item=self.menu, date=self.target_date - timedelta(days=1), qty_sold=100)
        forecast = calculate_forecast(self.menu, self.target_date)
        self.assertLessEqual(forecast.confidence, 50)
        
    def test_accuracy(self):
        self.assertEqual(calculate_accuracy(100, 100), 100)
        self.assertEqual(calculate_accuracy(90, 100), 90)
        self.assertEqual(calculate_accuracy(110, 100), 90)
        self.assertEqual(calculate_accuracy(250, 100), 0)
        # Division by zero prevention
        self.assertEqual(calculate_accuracy(0, 0), 100)
        self.assertEqual(calculate_accuracy(10, 0), 0)

    def test_forecast_tidak_negatif(self):
        DailySale.objects.create(menu_item=self.menu, date=self.target_date - timedelta(days=1), qty_sold=0)
        # Andaikata faktor hujan (0.90) dikali 0
        factor = ExternalFactor.objects.create(
            business=self.business, date=self.target_date,
            day_type='weekday', period='young_date', weather='rainy'
        )
        forecast = calculate_forecast(self.menu, self.target_date, factor)
        self.assertGreaterEqual(forecast.recommended_qty, 0)
