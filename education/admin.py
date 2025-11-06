from django.contrib import admin

from .models import HazardousComponent, LearningModule


@admin.register(HazardousComponent)
class HazardousComponentAdmin(admin.ModelAdmin):
	list_display = ("name", "hazard_level", "last_reviewed")
	list_filter = ("hazard_level",)
	search_fields = ("name", "overview")
	prepopulated_fields = {"slug": ("name",)}


@admin.register(LearningModule)
class LearningModuleAdmin(admin.ModelAdmin):
	list_display = ("title", "module_type", "estimated_read_time", "is_published")
	list_filter = ("module_type", "is_published")
	search_fields = ("title", "summary", "body")
	prepopulated_fields = {"slug": ("title",)}
	filter_horizontal = ("components",)
