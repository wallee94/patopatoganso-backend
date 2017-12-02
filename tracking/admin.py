from django.contrib import admin
from .models import Report, Publication


class PublicationAdmin(admin.ModelAdmin):
    list_display = ('report', 'url')


class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'date')


admin.site.register(Report, admin_class=ReportAdmin)
admin.site.register(Publication, admin_class=PublicationAdmin)
