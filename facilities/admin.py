from django.contrib import admin

from .models import Facility, FacilityAcceptedItem, FacilityService


class FacilityAcceptedItemInline(admin.TabularInline):
	model = FacilityAcceptedItem
	extra = 1


@admin.register(FacilityService)
class FacilityServiceAdmin(admin.ModelAdmin):
	list_display = ("name", "icon")
	search_fields = ("name",)


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
	list_display = ("name", "city", "state_province", "is_verified")
	list_filter = ("is_verified", "state_province", "services")
	search_fields = ("name", "city", "postal_code", "state_province")
	prepopulated_fields = {"slug": ("name",)}
	inlines = [FacilityAcceptedItemInline]
	filter_horizontal = ("services", "focus_components")


@admin.register(FacilityAcceptedItem)
class FacilityAcceptedItemAdmin(admin.ModelAdmin):
	list_display = ("facility", "category", "notes")
	list_filter = ("facility",)
	search_fields = ("category", "facility__name")
