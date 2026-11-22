from django import forms


def apply_bootstrap(form):
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            css = "form-check-input"
        elif isinstance(widget, forms.Select):
            css = "form-select"
        else:
            css = "form-control"
        existing = widget.attrs.get("class", "")
        if css not in existing.split():
            widget.attrs["class"] = f"{existing} {css}".strip()
    return form
