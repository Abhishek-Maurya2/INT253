from django.contrib import admin

from .models import DeviceCategory, DeviceMaterialEstimate, DeviceModel, DeviceSubmission


class DeviceMaterialEstimateInline(admin.TabularInline):
	model = DeviceMaterialEstimate
	extra = 1


@admin.register(DeviceCategory)
class DeviceCategoryAdmin(admin.ModelAdmin):
	list_display = ("name", "slug")
	search_fields = ("name",)
	prepopulated_fields = {"slug": ("name",)}


@admin.register(DeviceModel)
class DeviceModelAdmin(admin.ModelAdmin):
	list_display = ("manufacturer", "model_name", "category", "estimated_points")
	list_filter = ("category",)
	search_fields = ("manufacturer", "model_name")
	prepopulated_fields = {"slug": ("manufacturer", "model_name")}
	inlines = [DeviceMaterialEstimateInline]
	filter_horizontal = ("components",)


@admin.register(DeviceSubmission)
class DeviceSubmissionAdmin(admin.ModelAdmin):
	list_display = (
		"display_name",
		"drop_off_facility",
		"status",
		"estimated_credit_value",
		"submitted_at",
		"catalog_entry_created",
		"credits_awarded",
	)
	list_filter = ("status", "drop_off_facility", "catalog_entry_created", "credits_awarded")
	search_fields = ("custom_device_name", "device_model__model_name", "drop_off_facility__name")
	autocomplete_fields = ("device_model", "drop_off_facility", "user")
