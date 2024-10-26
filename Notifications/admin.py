from django.contrib import admin
from thrifto.models import UserProfile
from .models import Group, ContributionPeriod, Contribution, ContributionReminder, Notification


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'contribution_frequency', 'start_date', 'end_date')
    search_fields = ('name', 'creator__username')

@admin.register(ContributionPeriod)
class ContributionPeriodAdmin(admin.ModelAdmin):
    list_display = ('group', 'start_date', 'end_date', 'period_number')
    search_fields = ('group__name',)

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'amount', 'date_paid')
    search_fields = ('user__username', 'group__name')

@admin.register(ContributionReminder)
class ContributionReminderAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'period', 'date_sent')
    search_fields = ('user__username', 'group__name')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_dispaly = ('user')


