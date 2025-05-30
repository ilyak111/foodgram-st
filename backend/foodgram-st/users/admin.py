from django.contrib import admin
from .models import (
    CustomUser,
    Subscribe
)
from django.contrib.auth.admin import UserAdmin


class AdminCustomUser(UserAdmin):
    list_display = (
        'username',
        'first_name',
        'email',
        'is_staff'
    )
    ordering = ('email',)
    list_filter = (
        'is_staff',
        'is_active',
    )
    search_fields = (
        'username',
        'email',
    )


class AdminSubscribe(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')


admin.site.register(Subscribe, AdminSubscribe)
admin.site.register(CustomUser, AdminCustomUser)
