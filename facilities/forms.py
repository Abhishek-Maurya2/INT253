from django import forms

from .models import FacilityService


class FacilitySearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={
                "placeholder": "City, postal code, or facility name",
                "class": "flex-1 rounded-xl border-0 bg-transparent px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none",
            }
        ),
    )
    service = forms.ModelChoiceField(
        required=False,
        queryset=FacilityService.objects.none(),
        label="Filter by service",
        empty_label="All services",
        widget=forms.Select(
            attrs={
                "class": "w-full rounded-xl border-0 bg-transparent px-4 py-3 text-slate-100",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = FacilityService.objects.order_by("name")
