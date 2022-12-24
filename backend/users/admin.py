from django.contrib.admin import register
from django.contrib.auth import admin

from .models import User


@register(User)
class UserAdmin(admin.UserAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'password',
    )
    fields = (
        ('username', 'email',),
        ('first_name', 'last_name',),
    )
    fieldsets = []

    search_fields = (
        'username',
        'email',
    )
    list_filter = (
        'first_name',
        'email',
    )
