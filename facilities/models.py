from django.db import models
from django.utils.text import slugify


class FacilityService(models.Model):
	name = models.CharField(max_length=120, unique=True)
	description = models.TextField(blank=True)
	icon = models.CharField(max_length=60, blank=True, help_text="Heroicon or custom identifier")

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return self.name


class Facility(models.Model):
	name = models.CharField(max_length=200)
	slug = models.SlugField(max_length=210, unique=True)
	tagline = models.CharField(max_length=255, blank=True)
	description = models.TextField(blank=True)
	street_address = models.CharField(max_length=255)
	city = models.CharField(max_length=120)
	state_province = models.CharField(max_length=120)
	postal_code = models.CharField(max_length=20)
	country = models.CharField(max_length=60, default="India")
	latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	phone_number = models.CharField(max_length=30, blank=True)
	email = models.EmailField(blank=True)
	website = models.URLField(blank=True)
	hours_of_operation = models.JSONField(default=dict, blank=True)
	drop_off_instructions = models.TextField(blank=True)
	services = models.ManyToManyField(
		FacilityService,
		related_name="facilities",
		blank=True,
	)
	focus_components = models.ManyToManyField(
		'education.HazardousComponent',
		related_name='facilities',
		blank=True,
	)
	is_verified = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return self.name

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)

	@property
	def full_address(self) -> str:
		return f"{self.street_address}, {self.city}, {self.state_province} {self.postal_code}"


class FacilityAcceptedItem(models.Model):
	facility = models.ForeignKey(Facility, related_name="accepted_items", on_delete=models.CASCADE)
	category = models.CharField(max_length=150)
	notes = models.CharField(max_length=255, blank=True)

	class Meta:
		unique_together = ("facility", "category")
		ordering = ["category"]

	def __str__(self) -> str:
		return f"{self.category} @ {self.facility.name}"
