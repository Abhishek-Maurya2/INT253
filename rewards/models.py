from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Reward(models.Model):
	name = models.CharField(max_length=180)
	slug = models.SlugField(max_length=190, unique=True)
	summary = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	points_required = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
	image_url = models.URLField(blank=True)
	partner_url = models.URLField(blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["points_required"]

	def __str__(self) -> str:
		return self.name

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)


class RewardRedemption(models.Model):
	PENDING = "pending"
	FULFILLED = "fulfilled"
	CANCELLED = "cancelled"
	STATUS_CHOICES = [
		(PENDING, "Pending"),
		(FULFILLED, "Fulfilled"),
		(CANCELLED, "Cancelled"),
	]

	profile = models.ForeignKey('accounts.UserProfile', related_name="redemptions", on_delete=models.CASCADE)
	reward = models.ForeignKey(Reward, related_name="redemptions", on_delete=models.CASCADE)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
	points_spent = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
	requested_at = models.DateTimeField(auto_now_add=True)
	fulfilled_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		related_name="fulfilled_redemptions",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
	)
	fulfillment_notes = models.TextField(blank=True)

	class Meta:
		ordering = ["-requested_at"]

	def __str__(self) -> str:
		return f"{self.profile} -> {self.reward} ({self.status})"
