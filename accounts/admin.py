from django.contrib import admin

from .models import CreditTransaction, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = ("user", "phone_number", "total_credits", "newsletter_opt_in")
	search_fields = ("user__username", "user__email", "phone_number")
	list_filter = ("newsletter_opt_in",)


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
	list_display = ("profile", "amount", "reason", "source", "created_at")
	search_fields = ("profile__user__username", "reason", "source")
	list_filter = ("source",)
