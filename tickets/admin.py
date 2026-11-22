from django.contrib import admin

from .models import Ticket, TicketAttachment, TicketNote


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0


class TicketNoteInline(admin.TabularInline):
    model = TicketNote
    extra = 0


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "status", "created_by", "updated_at")
    list_filter = ("status", "project__company")
    search_fields = ("title", "description")
    inlines = [TicketAttachmentInline, TicketNoteInline]


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "uploaded_by", "created_at")


@admin.register(TicketNote)
class TicketNoteAdmin(admin.ModelAdmin):
    list_display = ("ticket", "author", "kind", "created_at")
