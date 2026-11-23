from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 1
    max_num = 1


admin.site.unregister(User)


@admin.register(User)
class AccountAdmin(UserAdmin):
    inlines = [ProfileInline]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "avatar"]
    list_select_related = ["user"]
    search_fields = ["user__username", "user__email"]
    list_filter = [("avatar", admin.EmptyFieldListFilter)]
    autocomplete_fields = ["user"]
