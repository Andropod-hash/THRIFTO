from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import os


def validate_file_type(file):
    """Validator to check if the file type is jpg, png, or pdf"""
    valid_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    ext = os.path.splitext(file.name)[1]  # Get the file extension
    if ext.lower() not in valid_extensions:
        raise ValidationError(_('Invalid file type. Only JPG, PNG, and PDF files are allowed.'))

def validate_file_size(file):
    """Validator to check if the file size is less than or equal to 10MB"""
    max_file_size = 10 * 1024 * 1024  # 10MB in bytes
    if file.size > max_file_size:
        raise ValidationError(_('File size cannot exceed 10MB.'))


class UserProfileManager(BaseUserManager):
    def create_user(self, email, username, password=None, full_name=None):
        """
        Create and return a user with validated required fields.
        """
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, full_name=full_name or "")  
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password, full_name=None):
        user = self.create_user(email=email, username=username, password=password, full_name=full_name)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user



class UserProfile(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=False)
    
    kyc_email = models.EmailField(blank=False)  
    confirm_kyc_email = models.EmailField()  
    kyc_phone_number = models.CharField(max_length=15, blank=False) 
    confirm_kyc_phone_number = models.CharField(max_length=15, blank=False)  
    
    address = models.TextField(blank=False)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    employer = models.CharField(max_length=255, blank=True)
    salary_range = models.CharField(max_length=50, blank=True)
    phone_number_confirmed = models.BooleanField(default=False)
    terms_agreed = models.BooleanField(default=False)
    kyc_confirmed = models.BooleanField(default=False)  
    email_confirmed = models.BooleanField(default=False)  


    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    file_upload = models.FileField(
        upload_to='uploads/',
        validators=[validate_file_type, validate_file_size],
        blank=True,
        null=True,
        help_text="Upload a JPG, PNG, or PDF file. Max size: 10MB."
    )

    groups = models.ManyToManyField(Group, related_name="user_profile_groups", blank=True)

    two_fa_code = models.CharField(max_length=6, blank=True, null=True)
    two_fa_code_expires = models.DateTimeField(blank=True, null=True)
    two_fa_verified = models.BooleanField(default=False)  

    objects = UserProfileManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']  


    def save(self, *args, **kwargs):
        # Automatically confirm KYC when terms are agreed
        if self.terms_agreed:
            self.kyc_confirmed = True
        
        # Automatically confirm email when KYC is confirmed
        if self.kyc_confirmed:
            self.email_confirmed = True
            
        super().save(*args, **kwargs)
    def __str__(self):
        return self.full_name


class Device(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    device_identifier = models.CharField(max_length=255)  
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    last_login = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.device_identifier} - {self.ip_address}"

class Group(models.Model):
    name = models.CharField(max_length=100)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='owned_groups', on_delete=models.CASCADE)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='members_groups', blank=True)

    def __str__(self):
        return self.name

  
    def save(self, *args, **kwargs):
        if self.pk is not None:  
            current_members_count = self.members.count()
            if current_members_count > 6:
                raise ValidationError("Members cannot be more than 6.")

        super().save(*args, **kwargs)