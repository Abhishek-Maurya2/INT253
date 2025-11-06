from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class DeviceCategory(models.Model):
	name = models.CharField(max_length=120, unique=True)
	slug = models.SlugField(max_length=130, unique=True)
	description = models.TextField(blank=True)
	icon = models.CharField(max_length=60, blank=True)

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return self.name

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)


class DeviceModel(models.Model):
	category = models.ForeignKey(DeviceCategory, related_name="devices", on_delete=models.CASCADE)
	manufacturer = models.CharField(max_length=120)
	model_name = models.CharField(max_length=150)
	slug = models.SlugField(max_length=180, unique=True)
	release_year = models.PositiveIntegerField(null=True, blank=True)
	description = models.TextField(blank=True)
	components = models.ManyToManyField(
		'education.HazardousComponent',
		related_name='device_models',
		blank=True,
	)
	estimated_points = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal("0.00"))
	estimated_recovery_notes = models.TextField(blank=True)
	image_url = models.URLField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["manufacturer", "model_name"]
		unique_together = ("manufacturer", "model_name")

	def __str__(self) -> str:
		return f"{self.manufacturer} {self.model_name}"

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(f"{self.manufacturer}-{self.model_name}")
		super().save(*args, **kwargs)


class DeviceMaterialEstimate(models.Model):
	device = models.ForeignKey(DeviceModel, related_name="material_estimates", on_delete=models.CASCADE)
	material_name = models.CharField(max_length=100)
	estimated_mass_grams = models.DecimalField(max_digits=10, decimal_places=2)
	estimated_value = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal("0.00"))

	class Meta:
		ordering = ["material_name"]

	def __str__(self) -> str:
		return f"{self.material_name} for {self.device}"


class DeviceSubmission(models.Model):
	DRAFT = "draft"
	PENDING = "pending"
	RECEIVED = "received"
	CREDITED = "credited"
	CANCELLED = "cancelled"
	STATUS_CHOICES = [
		(DRAFT, "Draft"),
		(PENDING, "Awaiting Drop-off"),
		(RECEIVED, "Received"),
		(CREDITED, "Credited"),
		(CANCELLED, "Cancelled"),
	]

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		related_name="device_submissions",
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
	)
	device_model = models.ForeignKey(
		DeviceModel,
		related_name="submissions",
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
	)
	custom_device_name = models.CharField(
		max_length=200,
		blank=True,
		help_text="Provide the device name if it is not listed.",
	)
	drop_off_facility = models.ForeignKey(
		'facilities.Facility',
		related_name='device_submissions',
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
	)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
	estimated_precious_metal_mass = models.DecimalField(
		max_digits=9,
		decimal_places=2,
		default=Decimal("0.00"),
		help_text="In grams",
	)
	estimated_credit_value = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal("0.00"))
	message_to_facility = models.CharField(max_length=280, blank=True)
	submitted_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-submitted_at"]

	def __str__(self) -> str:
		base_name = self.custom_device_name or (self.device_model and str(self.device_model)) or "Device"
		return f"Submission for {base_name}"

	@property
	def display_name(self) -> str:
		return self.custom_device_name or (self.device_model and str(self.device_model)) or "Custom device"
