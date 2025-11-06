from django.db import models
from django.utils.text import slugify


class HazardousComponent(models.Model):
	"""Core material/component tracked for educational pop-ups."""

	LOW = "low"
	MODERATE = "moderate"
	HIGH = "high"
	EXTREME = "extreme"
	HAZARD_LEVEL_CHOICES = [
		(LOW, "Low"),
		(MODERATE, "Moderate"),
		(HIGH, "High"),
		(EXTREME, "Extreme"),
	]

	name = models.CharField(max_length=150)
	slug = models.SlugField(max_length=160, unique=True)
	hazard_level = models.CharField(
		max_length=20,
		choices=HAZARD_LEVEL_CHOICES,
		default=MODERATE,
	)
	overview = models.TextField(help_text="High-level explanation of the component risk.")
	environmental_impact = models.TextField()
	human_health_impact = models.TextField()
	safe_handling_guidance = models.TextField(blank=True)
	last_reviewed = models.DateField(null=True, blank=True)
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


class LearningModule(models.Model):
	"""Curated educational narrative tied to hazardous components."""

	AWARENESS = "awareness"
	ACTION = "action"
	DEEP_DIVE = "deep_dive"
	MODULE_TYPE_CHOICES = [
		(AWARENESS, "Awareness"),
		(ACTION, "Actionable Guidance"),
		(DEEP_DIVE, "Deep Dive"),
	]

	title = models.CharField(max_length=200)
	slug = models.SlugField(max_length=210, unique=True)
	summary = models.CharField(max_length=255)
	body = models.TextField()
	module_type = models.CharField(
		max_length=20,
		choices=MODULE_TYPE_CHOICES,
		default=AWARENESS,
	)
	components = models.ManyToManyField(HazardousComponent, related_name="modules")
	estimated_read_time = models.PositiveIntegerField(default=3, help_text="In minutes")
	is_published = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["title"]

	def __str__(self) -> str:
		return self.title

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.title)
		super().save(*args, **kwargs)
