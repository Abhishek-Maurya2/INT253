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
	device_type = models.CharField(
		max_length=120,
		blank=True,
		help_text="General category such as phone, laptop, or monitor.",
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
	pickup_address = models.TextField(blank=True)
	submitted_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(auto_now=True)
	catalog_entry_created = models.BooleanField(default=False)
	credits_awarded = models.BooleanField(default=False)

	class Meta:
		ordering = ["-submitted_at"]

	def __str__(self) -> str:
		base_name = self.custom_device_name or (self.device_model and str(self.device_model)) or "Device"
		return f"Submission for {base_name}"

	@property
	def display_name(self) -> str:
		return self.custom_device_name or (self.device_model and str(self.device_model)) or "Custom device"

	def save(self, *args, **kwargs):
		previous_status = None
		if self.pk:
			previous_status = (
				DeviceSubmission.objects.filter(pk=self.pk).values_list("status", flat=True).first()
			)
		super().save(*args, **kwargs)

		status_changed = previous_status != self.status
		if not status_changed:
			return

		if self.status in {self.RECEIVED, self.CREDITED}:
			self._ensure_catalog_entry()

		if self.status == self.CREDITED:
			self._award_user_credits()

	def _ensure_catalog_entry(self) -> None:
		if self.catalog_entry_created:
			return

		if self.device_model:
			DeviceSubmission.objects.filter(pk=self.pk).update(catalog_entry_created=True)
			self.catalog_entry_created = True
			return

		device_name = (self.custom_device_name or "").strip()
		if not device_name and not self.device_type:
			return

		if not device_name:
			device_name = self.device_type

		parts = device_name.split()
		if len(parts) > 1:
			manufacturer = parts[0]
			model_value = " ".join(parts[1:])
		else:
			manufacturer = "Recovered"
			model_value = device_name

		category = None
		if self.device_type:
			category, _ = DeviceCategory.objects.get_or_create(name=self.device_type)
		elif self.device_model:
			category = self.device_model.category
		else:
			category, _ = DeviceCategory.objects.get_or_create(name="Uncategorized")

		slug_base = slugify(f"{manufacturer}-{model_value}") or slugify(device_name) or f"submission-{self.pk}"
		slug_value = slug_base
		counter = 1
		while DeviceModel.objects.filter(slug=slug_value).exists():
			slug_value = f"{slug_base}-{counter}"
			counter += 1

		estimated_points = self.estimated_credit_value or Decimal("0.00")
		description = self.message_to_facility or "Automatically generated from community submission."

		defaults = {
			"category": category,
			"slug": slug_value,
			"estimated_points": estimated_points,
			"estimated_recovery_notes": description,
		}
		device_model, created = DeviceModel.objects.get_or_create(
			manufacturer=manufacturer,
			model_name=model_value,
			defaults=defaults,
		)
		if not created:
			updated_fields = []
			if device_model.category != category:
				device_model.category = category
				updated_fields.append("category")
			if not device_model.estimated_recovery_notes and description:
				device_model.estimated_recovery_notes = description
				updated_fields.append("estimated_recovery_notes")
			if not device_model.estimated_points and estimated_points:
				device_model.estimated_points = estimated_points
				updated_fields.append("estimated_points")
			if updated_fields:
				device_model.save(update_fields=updated_fields)

		DeviceSubmission.objects.filter(pk=self.pk).update(
			device_model=device_model,
			catalog_entry_created=True,
		)
		self.device_model = device_model
		self.catalog_entry_created = True

	def _award_user_credits(self) -> None:
		if self.credits_awarded or not self.user_id:
			return

		amount = self.estimated_credit_value or Decimal("0.00")
		if amount <= 0:
			return

		try:
			profile = self.user.profile
		except AttributeError:
			from accounts.models import UserProfile  # local import to avoid circular
			profile, _ = UserProfile.objects.get_or_create(user=self.user)

		reason = f"Device submission credited ({self.display_name})"
		profile.adjust_credits(amount, reason=reason, source="device-submission")
		DeviceSubmission.objects.filter(pk=self.pk).update(credits_awarded=True)
		self.credits_awarded = True
