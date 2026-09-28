from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from grievances.models import Store, Role, UserProfile, EnquiryType, Grievance


class GrievanceReportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username='admin_report_test',
            email='admin_report@test.com',
            password='testpassword123'
        )
        self.role, _ = Role.objects.get_or_create(name='admin')
        self.profile, _ = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={
                'emp_id': 'ADM-REP-01',
                'role': self.role,
                'is_approved': True,
                'approval_status': 'approved'
            }
        )
        self.store = Store.objects.create(name='Matrix Store A')
        self.enquiry_type = EnquiryType.objects.create(name='Salary Grievance')
        self.client.force_login(self.user)

    def test_grievance_report_view(self):
        Grievance.objects.create(
            open_date='2026-09-28',
            emp_id='EMP-001',
            emp_name='John Doe',
            designation='Staff',
            department='HR',
            section='Ops',
            store=self.store,
            enquiry_type=self.enquiry_type,
            enquiry_received_by='Manager',
            enquiry_details='Salary discrepancy',
            current_status='open',
            created_by=self.user
        )
        url = reverse('grievance_report')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Store vs Enquiry Type Report')
        self.assertContains(response, 'Matrix Store A')
        self.assertContains(response, 'Salary Grievance')
        self.assertContains(response, 'Grand Total')

    def test_grievance_report_export(self):
        Grievance.objects.create(
            open_date='2026-09-28',
            emp_id='EMP-001',
            emp_name='John Doe',
            designation='Staff',
            department='HR',
            section='Ops',
            store=self.store,
            enquiry_type=self.enquiry_type,
            enquiry_received_by='Manager',
            enquiry_details='Salary discrepancy',
            current_status='open',
            created_by=self.user
        )
        url = reverse('grievance_report') + '?export=excel'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        content = response.content.decode('utf-8')
        self.assertIn('Particulars (Store Name)', content)
        self.assertIn('Matrix Store A', content)
        self.assertIn('Salary Grievance', content)
        self.assertIn('Grand Total', content)

    def test_regular_user_cannot_access_grievance_report(self):
        regular_role, _ = Role.objects.get_or_create(name='hr')
        regular_user = User.objects.create_user(
            username='staff_rep_user',
            password='testpassword123'
        )
        UserProfile.objects.create(
            user=regular_user,
            emp_id='STF-REP-01',
            role=regular_role,
            is_approved=True,
            approval_status='approved'
        )
        self.client.force_login(regular_user)
        url = reverse('grievance_report')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

