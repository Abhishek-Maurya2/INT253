from decimal import Decimal

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import DetailView, FormView, ListView, TemplateView

from facilities.models import Facility

from .forms import DeviceSubmissionForm
from .models import DeviceCategory, DeviceModel, DeviceSubmission


class DeviceCatalogView(ListView):
	model = DeviceModel
	paginate_by = 12
	template_name = "devices/device_catalog.html"
	context_object_name = "devices"

	def get_queryset(self):
		queryset = DeviceModel.objects.select_related("category").prefetch_related("components")
		query = self.request.GET.get("q")
		category_slug = self.request.GET.get("category")

		if query:
			queryset = queryset.filter(model_name__icontains=query)

		if category_slug:
			queryset = queryset.filter(category__slug=category_slug)

		return queryset.order_by("manufacturer", "model_name")

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["categories"] = (
			DeviceCategory.objects.filter(devices__isnull=False).distinct().order_by("name")
		)
		return context


class DeviceDetailView(DetailView):
    model = DeviceModel
    template_name = "devices/device_detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    context_object_name = "device"


class DeviceSubmissionView(FormView):
    template_name = "devices/device_submission.html"
    form_class = DeviceSubmissionForm
    success_url = reverse_lazy("devices:submission_success")

    def get_initial(self):
        initial = super().get_initial()
        facility_slug = self.request.GET.get("facility")
        if facility_slug:
            facility = Facility.objects.filter(slug=facility_slug).first()
            if facility:
                initial["drop_off_facility"] = facility.pk
        device_slug = self.request.GET.get("device")
        if device_slug:
            device = DeviceModel.objects.filter(slug=device_slug).first()
            if device:
                initial["device_model"] = device.pk
        return initial

    def form_valid(self, form):
        submission: DeviceSubmission = form.save(commit=False)
        if self.request.user.is_authenticated:
            submission.user = self.request.user

        if submission.device_model and (submission.estimated_credit_value or Decimal("0.00")) == Decimal("0.00"):
            submission.estimated_credit_value = submission.device_model.estimated_points

        submission.status = DeviceSubmission.PENDING
        submission.save()
        form.save_m2m()

        messages.success(
            self.request,
            "Thanks! Your device submission has been recorded. We will email you updates after the drop-off.",
        )

        self.submission = submission
        return super().form_valid(form)

    def get_success_url(self):
        url = super().get_success_url()
        if hasattr(self, "submission") and self.submission.drop_off_facility:
            return f"{url}?facility={self.submission.drop_off_facility.slug}"
        return url


class DeviceSubmissionSuccessView(TemplateView):
    template_name = "devices/device_submission_success.html"
