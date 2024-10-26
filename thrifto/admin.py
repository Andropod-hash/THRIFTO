from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile, Device, Employer, City, Country, SalaryRange, PasswordReset, Wallet
from django.core.exceptions import ValidationError

class UserProfileAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'phone_number', 'is_staff', 'is_superuser', 'is_active', 'two_fa_verified')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    filter_horizontal = ['groups']  
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone_number', 'address', 'city', 'country', 'employer', 'salary_range')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups')}),
        ('Confirmations', {'fields': ('email_confirmed',)}),  
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
    list_display = ('user', 'device_identifier')
    search_fields = ('user__email', 'device_identifier')


class CountryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')  
    search_fields = ('name',)  

class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'country')  
    search_fields = ('name',)  
    list_filter = ('country',)  

class SalaryRangeAdmin(admin.ModelAdmin):
    list_display = ('id', 'salary_range')  
    search_fields = ('salary_range',) 
    list_filter = ('salary_range',)  

class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ('user', 'reset_code', 'created_at', 'expires_at')


class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'encrypted_balance') 



admin.site.register(Wallet, WalletAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(SalaryRange, SalaryRangeAdmin)
admin.site.register(Employer)  
admin.site.register(PasswordReset, PasswordResetAdmin )
admin.site.register(Country, CountryAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(UserProfile, UserProfileAdmin)

