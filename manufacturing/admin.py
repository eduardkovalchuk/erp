 # -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Machine, Extruder, Division, ExtrusionType, Resin, MaterialType, Structure
# Register your models here.

class ExtruderInline(admin.TabularInline):
    model = Extruder


class MachineAdmin(admin.ModelAdmin):
    inlines = [ExtruderInline]

admin.site.register(Machine, MachineAdmin)
admin.site.register(Division)
admin.site.register(ExtrusionType)
admin.site.register(Resin)
admin.site.register(MaterialType)
admin.site.register(Structure)