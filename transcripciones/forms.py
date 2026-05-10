from django import forms


class DriveLinkForm(forms.Form):
    url = forms.URLField(
        label="Link de Drive",
        widget=forms.URLInput(
            attrs={
                "placeholder": "https://drive.google.com/...",
                "autofocus": True,
            }
        ),
    )
