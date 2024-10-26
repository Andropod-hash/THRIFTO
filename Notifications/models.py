from django.db import models
from django.conf import settings
from django.utils import timezone

class Notification(models.Model):
    USER_ACTIONS = [
        ('SIGNUP', 'Sign Up'),
        ('LOGIN', 'Login'),
        ('KYC_CONFIRMED', 'KYC Confirmed'),
        ('FORGET_PASSWORD', 'Forget_password'),
        ('PAYMENT_SUCCESSFUL', 'Payment Successful'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('CONTRIBUTION_SUCCESSFUL', 'Contribution Successful'),
        ('CYCLE_PAYMENT_RECEIVED', 'Cycle Payment Received'),
        ('FAILED_PAYMENT', 'Failed Payment'),
        ('WALLET_WITHDRAWAL', 'Wallet Withdrawal Successful'),
        ('WALLET_DEPOSIT', 'Wallet Deposit Successful'),
        ('GROUP_JOIN', 'Group Join Successful'),
        ('GROUP_REMOVAL', 'Group Removal Alert'),
        ('GROUP_INVITATION', 'Group Invitation Received'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=25, choices=USER_ACTIONS)  # Increased max_length
    created_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.action_type} notification for {self.user.username}"

    class Meta:
        ordering = ['-created_at']

class Group(models.Model):
    CONTRIBUTION_FREQUENCIES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    name = models.CharField(max_length=100)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='group_memberships', blank=True)
    contribution_frequency = models.CharField(max_length=10, choices=CONTRIBUTION_FREQUENCIES)
    start_date = models.DateField()
    end_date = models.DateField()
    contribution_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_periods = models.PositiveIntegerField(help_text="Total number of contribution periods")

    def __str__(self):
        return self.name

class ContributionPeriod(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='contribution_periods')
    start_date = models.DateField()
    end_date = models.DateField()
    period_number = models.PositiveIntegerField()

    class Meta:
        unique_together = ['group', 'period_number']

    def __str__(self):
        return f"{self.group.name} - Period {self.period_number}"

class Contribution(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateTimeField(default=timezone.now)
    periods_covered = models.ManyToManyField(ContributionPeriod, related_name='contributions')

    def __str__(self):
        return f"{self.user.username} - {self.group.name} - {self.date_paid}"

class ContributionReminder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    period = models.ForeignKey(ContributionPeriod, on_delete=models.CASCADE)
    date_sent = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reminder for {self.user.username} - {self.group.name} - Period {self.period.period_number}"

def record_contribution(user, group, amount, periods):
    contribution = Contribution.objects.create(
        group=group,
        user=user,
        amount=amount
    )
    contribution.periods_covered.add(*periods)
    return contribution

def get_user_payment_status(user, group):
    all_periods = ContributionPeriod.objects.filter(group=group).order_by('start_date')
    paid_periods = ContributionPeriod.objects.filter(group=group, contributions__user=user).distinct()
    unpaid_periods = all_periods.exclude(id__in=paid_periods)
    
    current_period = get_current_period(group, timezone.now().date())
    next_period = all_periods.filter(start_date__gt=current_period.end_date).first()
    
    return {
        'current_period_paid': current_period in paid_periods,
        'next_period_paid': next_period in paid_periods if next_period else None,
        'unpaid_periods': list(unpaid_periods),
        'total_unpaid': len(unpaid_periods),
    }

def get_current_period(group, date):
    return ContributionPeriod.objects.filter(
        group=group,
        start_date__lte=date,
        end_date__gte=date
    ).first()









# class Group(models.Model):
#     CONTRIBUTION_TYPES = [
#         ('1-minute', 'Every 1 Minute'),
#         ('5-minutes', 'Every 5 Minutes'),
#     ]

#     name = models.CharField(max_length=100)
#     creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_groups')
#     members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='group_memberships', blank=True)
#     contribution_type = models.CharField(max_length=10, choices=CONTRIBUTION_TYPES)
#     start_time = models.DateTimeField(default=timezone.now)
#     contribution_amount = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return self.name

# class Contribution(models.Model):
#     group = models.ForeignKey(Group, on_delete=models.CASCADE)
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
#     date = models.DateTimeField(default=timezone.now)
#     is_paid = models.BooleanField(default=False)

#     def __str__(self):
#         return f"{self.user.username} - {self.group.name} - {self.date}"

# class ContributionReminder(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     group = models.ForeignKey(Group, on_delete=models.CASCADE)
#     date_sent = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Reminder for {self.user.username} - {self.group.name} - {self.date_sent}"