from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        "placeholder": "you@example.com",
        "class": "w-full rounded-xl border border-slate-200 bg-white pl-12 pr-4 py-3 text-sm text-slate-700 placeholder-slate-400 shadow-sm transition focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:placeholder-slate-500",
    }))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "placeholder": "First name",
        "class": "w-full rounded-xl border border-slate-200 bg-white pl-12 pr-4 py-3 text-sm text-slate-700 placeholder-slate-400 shadow-sm transition focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:placeholder-slate-500",
    }))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "placeholder": "Last name",
        "class": "w-full rounded-xl border border-slate-200 bg-white pl-12 pr-4 py-3 text-sm text-slate-700 placeholder-slate-400 shadow-sm transition focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:placeholder-slate-500",
    }))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "placeholder": "Choose a username",
            "class": "w-full rounded-xl border border-slate-200 bg-white pl-12 pr-4 py-3 text-sm text-slate-700 placeholder-slate-400 shadow-sm transition focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:placeholder-slate-500",
        })
        self.fields["password1"].widget.attrs.update({
            "placeholder": "Create a password",
            "class": "w-full rounded-xl border border-slate-200 bg-white pl-12 pr-4 py-3 text-sm text-slate-700 placeholder-slate-400 shadow-sm transition focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:placeholder-slate-500",
        })
        self.fields["password2"].widget.attrs.update({
            "placeholder": "Confirm password",
            "class": "w-full rounded-xl border border-slate-200 bg-white pl-12 pr-4 py-3 text-sm text-slate-700 placeholder-slate-400 shadow-sm transition focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:placeholder-slate-500",
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "")
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
        return user


class StyledAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        "autofocus": True,
        "placeholder": "Username",
        "class": "w-full rounded-xl border border-slate-200 bg-white pl-12 pr-4 py-3 text-sm text-slate-700 placeholder-slate-400 shadow-sm transition focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:placeholder-slate-500",
    }))
    password = forms.CharField(strip=False, widget=forms.PasswordInput(attrs={
        "placeholder": "Password",
        "class": "w-full rounded-xl border border-slate-200 bg-white pl-12 pr-4 py-3 text-sm text-slate-700 placeholder-slate-400 shadow-sm transition focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:placeholder-slate-500",
    }))
