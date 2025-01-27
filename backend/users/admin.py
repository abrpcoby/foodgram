from django.contrib import admin
from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    list_display_links = ('username',)
    search_fields = ('username', 'email')
    list_filter = ('username', 'email')
    list_per_page = 50


admin.site.register(User, UserAdmin)
