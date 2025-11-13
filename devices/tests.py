from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import CreditTransaction
from devices.models import DeviceCategory, DeviceModel, DeviceSubmission
from education.models import HazardousComponent
from facilities.models import Facility, FacilityService


class DeviceSubmissionFlowTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.password = "test-pass-123"

		self.user = User.objects.create_user(
			username="resident",
			email="resident@example.com",
			password=self.password,
		)
		self.staff_user = User.objects.create_user(
			username="staff_admin",
			email="admin@example.com",
			password=self.password,
			is_staff=True,
		)

		self.component = HazardousComponent.objects.create(
			name="Lithium-ion Battery",
			hazard_level=HazardousComponent.HIGH,
			overview="Rechargeable energy storage posing thermal risk.",
			environmental_impact="Potential soil and water contamination.",
			human_health_impact="Skin irritation and respiratory issues on exposure.",
		)

		self.category = DeviceCategory.objects.create(name="Smartphone")
		self.device_model = DeviceModel.objects.create(
			category=self.category,
			manufacturer="EcoTech",
			model_name="Pulse X",
			estimated_points=Decimal("42.00"),
		)
		self.device_model.components.add(self.component)

		self.service = FacilityService.objects.create(name="Battery Consolidation")
		self.facility = Facility.objects.create(
			name="Green Loop Center",
			street_address="123 Circular Way",
			city="Metropolis",
			state_province="Delhi",
			postal_code="110001",
			description="Certified e-waste collection hub.",
			is_verified=True,
		)
		self.facility.services.add(self.service)
		self.facility.focus_components.add(self.component)

	def _submit_device(self):
		self.client.login(username=self.user.username, password=self.password)
		response = self.client.post(
			reverse("devices:submit"),
			data={
				"device_model": self.device_model.pk,
				"custom_device_name": "",
				"drop_off_facility": self.facility.pk,
				"estimated_precious_metal_mass": "12.5",
				"message_to_facility": "Handle with care",
				"agree_to_guidelines": "on",
			},
			follow=False,
		)
		return response

	def test_authenticated_user_submission_creates_pending_record(self):
		response = self._submit_device()
		expected_redirect = reverse("devices:submission_success") + f"?facility={self.facility.slug}"
		self.assertRedirects(response, expected_redirect)

		submission = DeviceSubmission.objects.get(user=self.user)
		self.assertEqual(submission.status, DeviceSubmission.PENDING)
		self.assertEqual(submission.estimated_credit_value, self.device_model.estimated_points)
		self.assertEqual(submission.drop_off_facility, self.facility)

		dashboard_response = self.client.get(reverse("accounts:user_dashboard"))
		self.assertEqual(dashboard_response.status_code, 200)
		self.assertIn("submissions", dashboard_response.context)
		self.assertIn(submission, dashboard_response.context["submissions"])

	def test_staff_review_and_credit_tracking_updates_profile(self):
		self._submit_device()
		submission = DeviceSubmission.objects.get(user=self.user)

		logged_in = self.client.login(username=self.staff_user.username, password=self.password)
		self.assertTrue(logged_in)

		admin_response = self.client.get(reverse("accounts:admin_dashboard"))
		self.assertEqual(admin_response.status_code, 200)

		profile = self.user.profile
		previous_balance = profile.total_credits

		profile.adjust_credits(
			submission.estimated_credit_value,
			reason="Submission credited",
			source="automated-test",
		)
		submission.status = DeviceSubmission.CREDITED
		submission.save(update_fields=["status"])

		submission.refresh_from_db()
		profile.refresh_from_db()

		self.assertEqual(submission.status, DeviceSubmission.CREDITED)
		self.assertEqual(
			profile.total_credits,
			previous_balance + submission.estimated_credit_value,
		)

		transactions = CreditTransaction.objects.filter(profile=profile)
		self.assertEqual(transactions.count(), 1)
		self.assertEqual(transactions.first().amount, submission.estimated_credit_value)
