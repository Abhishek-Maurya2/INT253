from django import forms

from .models import FacilityService


class FacilitySearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={
                "placeholder": "City, postal code, or facility name",
                "class": "w-full rounded-xl border-0 bg-transparent pl-12 pr-4 py-3 text-slate-700 placeholder-slate-400 focus:outline-none dark:text-slate-100 dark:placeholder-slate-500",
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
                "class": "w-full rounded-xl border-0 bg-transparent pl-12 pr-8 py-3 text-slate-700 focus:outline-none dark:text-slate-100",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = FacilityService.objects.order_by("name")
