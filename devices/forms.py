from decimal import Decimal

from django import forms

from facilities.models import Facility

from .models import DeviceModel, DeviceSubmission


class DeviceSubmissionForm(forms.ModelForm):
    agree_to_guidelines = forms.BooleanField(required=True, label="I agree to follow the drop-off guidelines")

    class Meta:
        model = DeviceSubmission
        fields = [
            "device_model",
            "custom_device_name",
            "drop_off_facility",
            "estimated_precious_metal_mass",
            "message_to_facility",
        ]
        widgets = {
            "device_model": forms.Select(attrs={
                "class": "w-full rounded-xl border-0 bg-transparent px-4 py-3 text-slate-100 focus:outline-none",
            }),
            "custom_device_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter model name",
                    "class": "w-full rounded-xl border-0 bg-transparent px-4 py-3 text-slate-100 focus:outline-none",
                }
            ),
            "drop_off_facility": forms.Select(attrs={
                "class": "w-full rounded-xl border-0 bg-transparent px-4 py-3 text-slate-100 focus:outline-none",
            }),
            "estimated_precious_metal_mass": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "0.01",
                    "class": "w-full rounded-xl border-0 bg-transparent px-4 py-3 text-slate-100 focus:outline-none",
                }
            ),
            "message_to_facility": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Add pickup or drop-off notes",
                    "class": "w-full rounded-xl border-0 bg-transparent px-4 py-3 text-slate-100 focus:outline-none",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["device_model"].queryset = DeviceModel.objects.order_by("manufacturer", "model_name")
        self.fields["drop_off_facility"].queryset = Facility.objects.order_by("city", "name")
        self.fields["estimated_precious_metal_mass"].initial = Decimal("0.00")
        self.fields["agree_to_guidelines"].widget.attrs.update(
            {
                "class": "h-4 w-4 rounded border-slate-700 bg-slate-900/40 text-sky-400 focus:ring-sky-400",
            }
        )

    def clean(self):
        cleaned_data = super().clean()
        device_model = cleaned_data.get("device_model")
        custom_device_name = cleaned_data.get("custom_device_name")

        if not device_model and not custom_device_name:
            raise forms.ValidationError("Select a known device model or provide a custom name.")

        return cleaned_data
