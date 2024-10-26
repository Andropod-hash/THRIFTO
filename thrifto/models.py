from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.core.mail import send_mail
from django.conf import settings
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import os
from dotenv import load_dotenv
from django.utils import timezone
import uuid


load_dotenv()

FERNET_KEY = os.getenv('FERNET_KEY')
if not FERNET_KEY:
    raise ValueError('FERNET_KEY environment variable is not set')


fernet = Fernet(FERNET_KEY)

class SalaryRange(models.Model):
    salary_range = models.CharField(max_length=100)
    currency = models.CharField(max_length=30)

    def __str__(self):
        return self.salary_range


class Employer(models.Model):
    name = models.CharField(max_length=100, unique=True)
    industry = models.CharField(max_length=100)
    sector = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class City(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='cities')

    def __str__(self):
        return self.name



def validate_file_type(file):
    """Validator to check if the file type is jpg, png, or pdf"""
    valid_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    ext = os.path.splitext(file.name)[1]  
    if ext.lower() not in valid_extensions:
        raise ValidationError(_('Invalid file type. Only JPG, PNG, and PDF files are allowed.'))

def validate_file_size(file):
    """Validator to check if the file size is less than or equal to 10MB"""
    max_file_size = 10 * 1024 * 1024  
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

        Wallet.objects.create(user=user)
        return user

    def create_superuser(self, email, username, password, full_name=None):
        user = self.create_user(email=email, username=username, password=password, full_name=full_name)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class UserProfile(AbstractBaseUser, PermissionsMixin):
    userId = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    
    """ KYC DETAILS """
    
    full_name = models.CharField(max_length=255)
    kyc_email = models.EmailField(blank=False)  
    phone_number = models.CharField(max_length=15, blank=False)
    address = models.TextField(blank=False)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)
    employer = models.ForeignKey(Employer, on_delete=models.SET_NULL, null=True) 
    salary_range = models.ForeignKey(SalaryRange, on_delete=models.SET_NULL, null=True)
    proof_of_salary = models.FileField(
        upload_to='uploads/',
        validators=[validate_file_type, validate_file_size],
        blank=True,
        null=True,
        help_text="Upload a JPG, PNG, or PDF file. Max size: 10MB."
    )
    terms_agreed = models.BooleanField(default=False)
    # kyc_confirmed = models.BooleanField(default=False)  
    email_confirmed = models.BooleanField(default=False)  


    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    groups = models.ManyToManyField(Group, related_name="user_profile_groups", blank=True)

    two_fa_code = models.CharField(max_length=6, blank=True, null=True)
    two_fa_code_expires = models.DateTimeField(blank=True, null=True)
    two_fa_verified = models.BooleanField(default=False) 
    two_fa_code_identifier = models.UUIDField(null=True, blank=True) 
    password_reset_token_expiry = models.DateTimeField(null=True, blank=True)


    objects = UserProfileManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']  


    def save(self, *args, **kwargs):
        # Automatically confirm KYC when terms are agreed
        if self.terms_agreed:
            self.term_agreed = True
        
        # # Automatically confirm email when KYC is confirmed
        # if self.kyc_confirmed:
        #     self.email_confirmed = True
            
        super().save(*args, **kwargs)
    def __str__(self):
        return self.full_name

class Wallet(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='wallet')
    encrypted_balance = models.BinaryField(default=fernet.encrypt(b'0.00'))  


    def get_balance(self):
        """ Decrypt and return the balance """
        decrpted_balance = fernet.decrypt(self.encrypted_balance)
        return float(decrypted_balance.decode())

    def update_balance(self):
        """ Decrypt and return the balance """
        new_balance = self.get_balance() + amount
        self.encrypted_balance = fernet.encrypt(str(new_balance).encode())
        
    def __str__(self):
        return f"Wallet for {self.user.username} = Balance: {self.get_balance()}"

class PasswordReset(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)  
    reset_code = models.CharField(max_length=64, unique=True)  
    expires_at = models.DateTimeField()  
    created_at = models.DateTimeField(auto_now_add=True)  

    def is_valid(self):
        """Check if the reset link is still valid (not expired)."""
        return timezone.now() < self.expires_at


class Device(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    device_identifier = models.CharField(max_length=255)  
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'device_identifier')

