from django.contrib import admin
from .models import *


class PriceAdmin(admin.ModelAdmin):
    list_display = ('report', 'price', 'first_date')
    readonly_fields = ('first_date',)
    raw_id_fields = ('report',)


class JobAdmin(admin.ModelAdmin):
    list_display = ('code', 'date')


class KeywordAdmin(admin.ModelAdmin):
    list_display = ('keyword', )


class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'last_date', 'last_price')


admin.site.register(Report, admin_class=ReportAdmin)
admin.site.register(Price, admin_class=PriceAdmin)
admin.site.register(Job, admin_class=JobAdmin)
admin.site.register(Keyword, admin_class=KeywordAdmin)
