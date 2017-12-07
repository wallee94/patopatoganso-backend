from django.contrib import admin
from .models import Report, Price


class PriceAdmin(admin.ModelAdmin):
    list_display = ('report', 'price', 'date')


class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'last_date')


admin.site.register(Report, admin_class=ReportAdmin)
admin.site.register(Price, admin_class=PriceAdmin)
