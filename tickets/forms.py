from pathlib import Path

from django import forms
from django.core.exceptions import ValidationError
from PIL import Image

from accounts.bootstrap import apply_bootstrap

from .access import projects_for_new_ticket
from .models import Ticket

ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def validate_ticket_image(uploaded):
    suffix = Path(uploaded.name).suffix.lower()
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        raise ValidationError("Upload a jpg, png, gif, or webp image.")
    if uploaded.size > MAX_IMAGE_BYTES:
        raise ValidationError("Images must be 5 MB or smaller.")
    try:
        image = Image.open(uploaded)
        image.verify()
    except Exception as exc:
        raise ValidationError("Upload a valid image.") from exc
    finally:
        uploaded.seek(0)


class TicketCreateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["project", "title", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, actor, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"].queryset = projects_for_new_ticket(actor).select_related(
            "company"
        )
        apply_bootstrap(self)


class NoteForm(forms.Form):
    body = forms.CharField(label="Note", widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap(self)


class StatusForm(forms.Form):
    status = forms.ChoiceField(choices=Ticket.Status.choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap(self)
