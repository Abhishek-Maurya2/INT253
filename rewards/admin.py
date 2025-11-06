from django.contrib import admin

from .models import Reward, RewardRedemption


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
	list_display = ("name", "points_required", "is_active")
	list_filter = ("is_active",)
	search_fields = ("name", "summary")
	prepopulated_fields = {"slug": ("name",)}


@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
	list_display = ("profile", "reward", "status", "points_spent", "requested_at")
	list_filter = ("status",)
	search_fields = ("profile__user__username", "reward__name")
	autocomplete_fields = ("profile", "reward", "fulfilled_by")
