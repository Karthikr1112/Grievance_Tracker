from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from grievances.models import Role, UserProfile
from food_waste.models import FoodWasteStore, FoodWasteEntry, get_current_month


class FoodWasteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='testpassword123'
        )
        self.role, _ = Role.objects.get_or_create(name='admin')
        self.profile, _ = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={
                'emp_id': 'ADM-001',
                'role': self.role,
                'is_approved': True,
                'approval_status': 'approved'
            }
        )
        self.store = FoodWasteStore.objects.create(name='Test Food Waste Store 101')
        self.client.force_login(self.user)

    def test_food_waste_create_get(self):
        url = reverse('food_waste_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Daily Food Waste Entry')
        self.assertContains(response, 'Test Food Waste Store 101')
        self.assertContains(response, 'Breakfast')
        self.assertContains(response, 'Lunch')
        self.assertContains(response, 'Dinner')
        self.assertContains(response, 'Shortage')
        self.assertContains(response, 'Food Quality Review')
        # Check current month is present as an option
        curr_month = get_current_month()
        self.assertContains(response, f'value="{curr_month}"')

    def test_food_waste_create_post(self):
        url = reverse('food_waste_create')
        curr_month = get_current_month()
        data = {
            'store': self.store.id,
            'date': '2026-09-28',
            'month': curr_month,
            # Breakfast
            'breakfast_menu': 'Idli, Vada, Sambar',
            'breakfast_received_kg': '25.50',
            'breakfast_wastage_kg': '2.25',
            'breakfast_shortage': 'yes',
            'breakfast_shortage_count': 5,
            'breakfast_review': 'good',
            'breakfast_remarks': 'Food was warm and on time.',
            # Lunch
            'lunch_menu': 'Rice, Sambar, Poriyal, Curd',
            'lunch_received_kg': '50.00',
            'lunch_wastage_kg': '4.50',
            'lunch_shortage': 'no',
            'lunch_shortage_count': '',
            'lunch_review': 'excellent',
            'lunch_remarks': 'Staff enjoyed the meals.',
            # Dinner
            'dinner_menu': 'Chapathi, Dal, Rice',
            'dinner_received_kg': '30.00',
            'dinner_wastage_kg': '1.50',
            'dinner_shortage': 'no',
            'dinner_shortage_count': '',
            'dinner_review': 'not_good',
            'dinner_remarks': 'Chapathis were hard.',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirects after success
        self.assertEqual(FoodWasteEntry.objects.count(), 1)
        entry = FoodWasteEntry.objects.first()
        self.assertEqual(entry.store, self.store)
        self.assertEqual(entry.month, curr_month)
        self.assertEqual(float(entry.total_received_kg), 105.50)
        self.assertEqual(float(entry.total_wastage_kg), 8.25)
        self.assertEqual(entry.breakfast_shortage, 'yes')
        self.assertEqual(entry.breakfast_shortage_count, 5)
        self.assertEqual(entry.dinner_review, 'not_good')
        self.assertEqual(entry.dinner_remarks, 'Chapathis were hard.')

    def test_food_waste_list_view(self):
        curr_month = get_current_month()
        FoodWasteEntry.objects.create(
            store=self.store,
            date='2026-09-28',
            month=curr_month,
            breakfast_menu='Dosa',
            breakfast_received_kg=20,
            breakfast_wastage_kg=2,
            created_by=self.user
        )
        url = reverse('food_waste_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Food Waste Store 101')
        self.assertContains(response, 'Dosa')

    def test_food_waste_csv_export(self):
        curr_month = get_current_month()
        FoodWasteEntry.objects.create(
            store=self.store,
            date='2026-09-28',
            month=curr_month,
            breakfast_menu='Pongal',
            breakfast_received_kg=15,
            breakfast_wastage_kg=1,
            created_by=self.user
        )
        url = reverse('food_waste_list') + '?export=excel'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        content = response.content.decode('utf-8')
        self.assertIn('Test Food Waste Store 101', content)
        self.assertIn('Pongal', content)

    def test_food_waste_report_view(self):
        curr_month = get_current_month()
        FoodWasteEntry.objects.create(
            store=self.store,
            date='2026-09-28',
            month=curr_month,
            breakfast_received_kg=25,
            breakfast_wastage_kg=2.5,
            lunch_received_kg=50,
            lunch_wastage_kg=5,
            dinner_received_kg=25,
            dinner_wastage_kg=2.5,
            created_by=self.user
        )
        url = reverse('food_waste_report')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Store-Wise Food Waste Report')
        self.assertContains(response, 'Grand Total')
        self.assertContains(response, 'Test Food Waste Store 101')

    def test_food_waste_report_export(self):
        curr_month = get_current_month()
        FoodWasteEntry.objects.create(
            store=self.store,
            date='2026-09-28',
            month=curr_month,
            breakfast_received_kg=25,
            breakfast_wastage_kg=2.5,
            created_by=self.user
        )
        url = reverse('food_waste_report') + '?export=excel'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        content = response.content.decode('utf-8')
        self.assertIn('Particulars (Store Name)', content)
        self.assertIn('Test Food Waste Store 101', content)
        self.assertIn('Grand Total', content)
        self.assertNotIn('Logs Count', content)

    def test_regular_user_only_sees_own_records(self):
        regular_role, _ = Role.objects.get_or_create(name='hr')
        regular_user = User.objects.create_user(
            username='staff_user',
            password='testpassword123'
        )
        UserProfile.objects.create(
            user=regular_user,
            emp_id='STF-001',
            role=regular_role,
            is_approved=True,
            approval_status='approved'
        )

        curr_month = get_current_month()
        # Admin entry
        FoodWasteEntry.objects.create(
            store=self.store,
            date='2026-09-27',
            month=curr_month,
            breakfast_menu='Admin Special Upma',
            created_by=self.user
        )
        # Staff entry
        FoodWasteEntry.objects.create(
            store=self.store,
            date='2026-09-28',
            month=curr_month,
            breakfast_menu='Staff Idli Sambar',
            created_by=regular_user
        )

        # Login as regular user
        self.client.force_login(regular_user)
        url = reverse('food_waste_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Staff Idli Sambar')
        self.assertNotContains(response, 'Admin Special Upma')

        # Regular user cannot access food waste report
        rep_url = reverse('food_waste_report')
        rep_response = self.client.get(rep_url)
        self.assertEqual(rep_response.status_code, 302)
        self.assertRedirects(rep_response, reverse('dashboard'))

    def test_admin_sees_all_records(self):
        regular_role, _ = Role.objects.get_or_create(name='hr')
        regular_user = User.objects.create_user(
            username='staff_user2',
            password='testpassword123'
        )
        UserProfile.objects.create(
            user=regular_user,
            emp_id='STF-002',
            role=regular_role,
            is_approved=True,
            approval_status='approved'
        )

        curr_month = get_current_month()
        FoodWasteEntry.objects.create(
            store=self.store,
            date='2026-09-27',
            month=curr_month,
            breakfast_menu='Admin Meal Item',
            created_by=self.user
        )
        FoodWasteEntry.objects.create(
            store=self.store,
            date='2026-09-28',
            month=curr_month,
            breakfast_menu='Staff Meal Item',
            created_by=regular_user
        )

        # Admin logged in
        self.client.force_login(self.user)
        url = reverse('food_waste_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Meal Item')
        self.assertContains(response, 'Staff Meal Item')

        # Admin can access report
        rep_url = reverse('food_waste_report')
        rep_response = self.client.get(rep_url)
        self.assertEqual(rep_response.status_code, 200)


