from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
	avatar_url = models.URLField(blank=True)
	phone_number = models.CharField(max_length=20, blank=True)
	home_location = models.CharField(max_length=255, blank=True)
	total_credits = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
	newsletter_opt_in = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["user__username"]

	def __str__(self) -> str:
		return f"Profile for {self.user.get_full_name() or self.user.username}"

	def adjust_credits(self, amount: Decimal, *, reason: str = "", source: str = "manual"):
		self.total_credits = (self.total_credits or Decimal("0.00")) + amount
		self.save(update_fields=["total_credits"])
		CreditTransaction.objects.create(
			profile=self,
			amount=amount,
			reason=reason,
			source=source,
		)


class CreditTransaction(models.Model):
	profile = models.ForeignKey(UserProfile, related_name="transactions", on_delete=models.CASCADE)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	reason = models.CharField(max_length=255, blank=True)
	source = models.CharField(max_length=120, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"{self.amount} credits for {self.profile}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
	if created:
		UserProfile.objects.create(user=instance)
