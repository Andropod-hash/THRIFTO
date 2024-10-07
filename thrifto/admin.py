from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile, Device, Group
from django.core.exceptions import ValidationError

class UserProfileAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'phone_number', 'is_staff', 'kyc_confirmed', 'is_superuser', 'is_active', 'two_fa_verified')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    filter_horizontal = ['groups']  
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone_number', 'address', 'city', 'country', 'employer', 'salary_range')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups')}),
        ('Confirmations', {'fields': ('email_confirmed', 'phone_number_confirmed')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'phone_number', 'address', 'city', 'country', 'employer', 'salary_range', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'full_name', 'phone_number')
    ordering = ('email',)

class DeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_identifier', 'ip_address', 'last_login')
    search_fields = ('user__email', 'device_identifier', 'ip_address')
    list_filter = ('last_login',)

class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'admin', 'get_members_count')
    
    def save_model(self, request, obj, form, change):
        # If admin is not set, assign the creator as the admin
        if not obj.admin:
            obj.admin = request.user
        super().save_model(request, obj, form, change)

    def get_members_count(self, obj):
        return obj.members.count()
    get_members_count.short_description = 'Members Count'

admin.site.register(Device, DeviceAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
