from django.contrib import admin
from .models import Ingredient


class AdminIngredient(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_filter = ('measurement_unit',)
    search_fields = ('name',)


admin.site.register(Ingredient, AdminIngredient)
