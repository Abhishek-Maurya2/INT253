from decimal import Decimal

from django import forms

from facilities.models import Facility

from .models import DeviceCategory, DeviceModel, DeviceSubmission


class DeviceSubmissionForm(forms.ModelForm):
    agree_to_guidelines = forms.BooleanField(required=True, label="I agree to follow the drop-off guidelines")
    device_category = forms.ModelChoiceField(
        required=False,
        queryset=DeviceCategory.objects.none(),
        label="Device type",
        widget=forms.Select(
            attrs={
                "class": "w-full appearance-none rounded-xl border-0 bg-transparent pl-12 pr-12 py-3 text-sm text-slate-700 focus:outline-none dark:text-slate-100",
            }
        ),
    )
    custom_device_type = forms.CharField(
        required=False,
        label="Custom device type",
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. Smart speaker",
                "class": "w-full rounded-xl border-0 bg-transparent pl-12 pr-4 py-3 text-sm text-slate-700 placeholder-slate-400 focus:outline-none dark:text-slate-100 dark:placeholder-slate-500",
            }
        ),
    )

    class Meta:
        model = DeviceSubmission
        fields = [
            "device_model",
            "device_type",
            "custom_device_name",
            "drop_off_facility",
            "pickup_address",
            "estimated_precious_metal_mass",
            "estimated_credit_value",
            "message_to_facility",
        ]
        widgets = {
            "device_model": forms.Select(attrs={
                "class": "w-full appearance-none rounded-xl border-0 bg-transparent pl-12 pr-12 py-3 text-sm text-slate-700 focus:outline-none dark:text-slate-100",
            }),
            "device_type": forms.HiddenInput(),
            "custom_device_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter device name or model number",
                    "class": "w-full rounded-xl border-0 bg-transparent pl-12 pr-4 py-3 text-sm text-slate-700 placeholder-slate-400 focus:outline-none dark:text-slate-100 dark:placeholder-slate-500",
                }
            ),
            "drop_off_facility": forms.Select(attrs={
                "class": "w-full appearance-none rounded-xl border-0 bg-transparent pl-12 pr-12 py-3 text-sm text-slate-700 focus:outline-none dark:text-slate-100",
            }),
            "pickup_address": forms.Textarea(
                attrs={
                    "rows": 2,
                    "placeholder": "Street, city, postal code",
                    "class": "w-full rounded-xl border-0 bg-transparent pl-12 pr-4 py-3 text-sm text-slate-700 placeholder-slate-400 focus:outline-none dark:text-slate-100 dark:placeholder-slate-500",
                }
            ),
            "estimated_precious_metal_mass": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "0.01",
                    "class": "w-full rounded-xl border-0 bg-transparent pl-12 pr-4 py-3 text-sm text-slate-700 focus:outline-none dark:text-slate-100",
                }
            ),
            "estimated_credit_value": forms.TextInput(
                attrs={
                    "readonly": "readonly",
                    "class": "w-full rounded-xl border-0 bg-transparent pl-12 pr-4 py-3 text-sm text-slate-700 focus:outline-none dark:text-slate-100",
                }
            ),
            "message_to_facility": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Add pickup or drop-off notes",
                    "class": "w-full rounded-xl border-0 bg-transparent pl-12 pr-4 py-3 text-sm text-slate-700 placeholder-slate-400 focus:outline-none dark:text-slate-100 dark:placeholder-slate-500",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["device_model"].queryset = DeviceModel.objects.order_by("manufacturer", "model_name")
        self.fields["device_category"].queryset = DeviceCategory.objects.order_by("name")
        self.fields["drop_off_facility"].queryset = Facility.objects.order_by("city", "name")
        self.fields["estimated_precious_metal_mass"].initial = Decimal("0.00")
        self.fields["agree_to_guidelines"].widget.attrs.update(
            {
                "class": "h-4 w-4 rounded border-slate-300 text-sky-500 focus:ring-sky-400 dark:border-slate-600 dark:bg-slate-900/60",
            }
        )
        self.fields["estimated_credit_value"].initial = Decimal("0.00")

    def clean(self):
        cleaned_data = super().clean()
        device_model = cleaned_data.get("device_model")
        custom_device_name = cleaned_data.get("custom_device_name")
        device_category = cleaned_data.get("device_category")
        custom_device_type = cleaned_data.get("custom_device_type", "").strip()

        if custom_device_type:
            cleaned_data["device_type"] = custom_device_type
        elif device_category is not None:
            cleaned_data["device_type"] = device_category.name
        else:
            cleaned_data["device_type"] = ""

        if not device_model and not custom_device_name:
            raise forms.ValidationError("Select a known device model or provide a custom name.")

        return cleaned_data

    def save(self, commit=True):
        instance: DeviceSubmission = super().save(commit=False)
        device_type = self.cleaned_data.get("device_type", "")
        if device_type:
            instance.device_type = device_type
        if commit:
            instance.save()
        self.save_m2m()
        return instance
