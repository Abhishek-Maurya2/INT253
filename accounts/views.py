from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from devices.models import DeviceModel, DeviceSubmission
from education.models import LearningModule
from facilities.models import Facility
from rewards.models import Reward

from .forms import StyledAuthenticationForm, UserRegistrationForm
from .models import UserProfile


def redirect_authenticated_user(request: HttpRequest) -> HttpResponse:
	if request.user.is_staff:
		return redirect("accounts:admin_dashboard")
	return redirect("accounts:user_dashboard")


def register(request: HttpRequest) -> HttpResponse:
	if request.user.is_authenticated:
		return redirect_authenticated_user(request)

	if request.method == "POST":
		form = UserRegistrationForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, "Welcome aboard! Your account is ready.")
			return redirect_authenticated_user(request)
	else:
		form = UserRegistrationForm()

	return render(request, "accounts/register.html", {"form": form})


def sign_in(request: HttpRequest) -> HttpResponse:
	if request.user.is_authenticated:
		return redirect_authenticated_user(request)

	next_url = request.GET.get("next")
	if request.method == "POST":
		form = StyledAuthenticationForm(request, data=request.POST)
		if form.is_valid():
			user = form.get_user()
			login(request, user)
			messages.success(request, "Signed in successfully.")
			target = request.POST.get("next") or next_url
			if target:
				return redirect(target)
			if user.is_staff:
				return redirect("accounts:admin_dashboard")
			return redirect("accounts:user_dashboard")
	else:
		form = StyledAuthenticationForm(request, initial={"next": next_url})

	return render(request, "accounts/login.html", {"form": form, "next": next_url})


@login_required
def sign_out(request: HttpRequest) -> HttpResponse:
	if request.method == "POST":
		logout(request)
		messages.info(request, "You have been signed out.")
	return redirect("facilities:home")


@login_required
def user_dashboard(request: HttpRequest) -> HttpResponse:
	profile, _ = UserProfile.objects.get_or_create(user=request.user)
	submissions = DeviceSubmission.objects.filter(user=request.user)[:5]
	nearby_facilities = Facility.objects.all()[:3]
	modules = LearningModule.objects.all()[:3]
	rewards = Reward.objects.all()[:3]

	return render(
		request,
		"accounts/user_dashboard.html",
		{
			"profile": profile,
			"submissions": submissions,
			"facilities": nearby_facilities,
			"modules": modules,
			"rewards": rewards,
		},
	)


def staff_check(user) -> bool:
	return user.is_staff


@login_required
@user_passes_test(staff_check)
def admin_dashboard(request: HttpRequest) -> HttpResponse:
	facility_total = Facility.objects.count()
	device_total = DeviceModel.objects.count()
	submission_total = DeviceSubmission.objects.count()
	reward_total = Reward.objects.count()
	recent_submissions = (
		DeviceSubmission.objects.select_related("user", "drop_off_facility", "device_model")
		.order_by("-submitted_at")[:6]
	)

	actions = [
		{
			"title": "Manage Facilities",
			"description": "Add new collection points or update existing facility records.",
			"href": reverse("admin:facilities_facility_changelist"),
		},
		{
			"title": "Device Catalog",
			"description": "Curate device models, materials, and recovery insights.",
			"href": reverse("admin:devices_devicemodel_changelist"),
		},
		{
			"title": "Learning Modules",
			"description": "Publish educational content and hazardous component details.",
			"href": reverse("admin:education_learningmodule_changelist"),
		},
		{
			"title": "Rewards",
			"description": "Adjust incentives and track redemption options.",
			"href": reverse("admin:rewards_reward_changelist"),
		},
	]

	quick_add = [
		{
			"label": "New Facility",
			"href": reverse("admin:facilities_facility_add"),
		},
		{
			"label": "New Device Model",
			"href": reverse("admin:devices_devicemodel_add"),
		},
		{
			"label": "New Learning Module",
			"href": reverse("admin:education_learningmodule_add"),
		},
		{
			"label": "New Reward",
			"href": reverse("admin:rewards_reward_add"),
		},
	]

	return render(
		request,
		"accounts/admin_dashboard.html",
		{
			"facility_total": facility_total,
			"device_total": device_total,
			"submission_total": submission_total,
			"reward_total": reward_total,
			"actions": actions,
			"quick_add": quick_add,
			"recent_submissions": recent_submissions,
		},
	)
