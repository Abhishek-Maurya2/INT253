from django.db.models import Count, Q
from django.views.generic import DetailView, ListView, TemplateView

from devices.forms import DeviceSubmissionForm
from devices.models import DeviceModel
from education.models import HazardousComponent, LearningModule

from .forms import FacilitySearchForm
from .models import Facility


class HomeView(TemplateView):
	template_name = "facilities/home.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context.update(
			{
				"search_form": FacilitySearchForm(self.request.GET or None),
				"total_facilities": Facility.objects.count(),
				"total_components": HazardousComponent.objects.count(),
				"total_device_models": DeviceModel.objects.count(),
				"featured_facilities": Facility.objects.filter(is_verified=True)[:3],
				"featured_modules": LearningModule.objects.filter(is_published=True)[:3],
			}
		)
		return context


class FacilityListView(ListView):
	model = Facility
	paginate_by = 9
	template_name = "facilities/facility_list.html"
	context_object_name = "facilities"

	def get_queryset(self):
		queryset = (
			Facility.objects.select_related()
			.prefetch_related("services", "focus_components", "accepted_items")
			.annotate(total_services=Count("services"))
		)
		query = self.request.GET.get("query") or self.request.GET.get("q")
		service_slug = self.request.GET.get("service")

		if query:
			queryset = queryset.filter(
				Q(name__icontains=query)
				| Q(city__icontains=query)
				| Q(postal_code__icontains=query)
				| Q(state_province__icontains=query)
			)

		if service_slug:
			queryset = queryset.filter(services__id=service_slug)

		return queryset.distinct().order_by("name")

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["search_form"] = FacilitySearchForm(self.request.GET or None)
		context["active_query"] = self.request.GET.get("query") or self.request.GET.get("q") or ""
		return context


class FacilityDetailView(DetailView):
	model = Facility
	template_name = "facilities/facility_detail.html"
	context_object_name = "facility"
	slug_field = "slug"
	slug_url_kwarg = "slug"

	def get_queryset(self):
		return (
			Facility.objects.select_related()
			.prefetch_related("services", "focus_components", "accepted_items")
			.all()
		)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		facility = self.object
		context["device_submission_form"] = DeviceSubmissionForm(
			initial={"drop_off_facility": facility},
		)
		context["related_modules"] = (
			LearningModule.objects.filter(components__in=facility.focus_components.all())
			.distinct()
			.order_by("title")
		)
		return context
