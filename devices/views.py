import json
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, FormView, ListView, TemplateView

from facilities.models import Facility
from ewaste.services.gemini import estimate_device_metrics

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

        ai_payload = {
            "device_name": submission.display_name,
            "device_category": submission.device_model.category.name if submission.device_model else submission.device_type,
            "facility_name": submission.drop_off_facility.name if submission.drop_off_facility else None,
            "user_estimated_mass": form.cleaned_data.get("estimated_precious_metal_mass"),
            "components": [component.name for component in submission.device_model.components.all()] if submission.device_model else [],
            "user_notes": submission.message_to_facility,
            "device_type": submission.device_type,
            "pickup_address": submission.pickup_address,
        }
        ai_estimate = estimate_device_metrics(ai_payload)
        if ai_estimate:
            mass = ai_estimate.get("estimated_precious_metal_mass_grams")
            credit_value = ai_estimate.get("estimated_credit_value")

            if mass is not None:
                try:
                    submission.estimated_precious_metal_mass = Decimal(mass)
                except (InvalidOperation, TypeError):
                    pass

            if credit_value is not None:
                try:
                    submission.estimated_credit_value = Decimal(credit_value)
                except (InvalidOperation, TypeError):
                    pass

            submission.save(update_fields=[
                "estimated_precious_metal_mass",
                "estimated_credit_value",
                "updated_at",
            ])

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


class DeviceEstimateView(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "invalid_payload"}, status=400)

        ai_payload = {
            "device_name": payload.get("device_name"),
            "device_category": payload.get("device_category"),
            "device_type": payload.get("device_type"),
            "facility_name": payload.get("facility_name"),
            "user_estimated_mass": payload.get("user_estimated_mass"),
            "components": payload.get("components", []),
            "user_notes": payload.get("user_notes"),
            "pickup_address": payload.get("pickup_address"),
        }

        ai_estimate = estimate_device_metrics(ai_payload)
        if not ai_estimate:
            return JsonResponse({"success": False}, status=422)

        response_data = {"success": True}

        mass = ai_estimate.get("estimated_precious_metal_mass_grams")
        if mass is not None:
            response_data["estimated_precious_metal_mass_grams"] = str(mass)

        credit_value = ai_estimate.get("estimated_credit_value")
        if credit_value is not None:
            response_data["estimated_credit_value"] = str(credit_value)

        confidence = ai_estimate.get("confidence")
        if confidence:
            response_data["confidence"] = confidence

        return JsonResponse(response_data)
