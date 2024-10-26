from rest_framework import serializers
from django.utils import timezone
import secrets
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import UserProfile, Device,  Group, Country, City, Employer, SalaryRange, PasswordReset
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from Notifications.utilis import log_and_send_email
from django.utils.translation import gettext as _

class UserRegistrationSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'password1', 'password2',
        ]

    def validate(self, attrs):
        # To Check if passwords match
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        return attrs

    def create(self, validated_data):
        # To Extract password fields and remove them from validated_data
        password1 = validated_data.pop('password1')
        validated_data.pop('password2')  

        # To Create user profile
        user = UserProfile.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=password1,
        )

        return user

class KYCSerializer(serializers.ModelSerializer):
    confirm_email = serializers.EmailField(write_only=True)
    confirm_phone_number = serializers.CharField(write_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'full_name',
            'kyc_email', 'confirm_email', 
            'phone_number', 'confirm_phone_number', 
            'address', 'city', 'country', 'employer', 
            'salary_range', 'terms_agreed'
        ]

        extra_kwargs = {
            'kyc_email': {'required': True, 'error_messages': {'required': 'KYC email is required.'}},
            'phone_number': {'required': True, 'error_messages': {'required': 'KYC phone number is required.'}},
            'address': {'required': True, 'error_messages': {'required': 'Address is required.'}},
            'city': {'required': True, 'error_messages': {'required': 'City is required.'}},
            'country': {'required': True, 'error_messages': {'required': 'Country is required.'}},
            'employer': {'required': True, 'error_messages': {'required': 'Employer information is required.'}},
            'salary_range': {'required': True, 'error_messages': {'required': 'Salary range is required.'}},
            # 'proof_of_salary': {'required': True, 'error_messages': {'required': 'Proof of salary is required.'}},
            'terms_agreed': {'required': True, 'error_messages': {'required': 'You must agree to the terms.'}},
        }

    def validate(self, attrs):
        # Check if KYC has been previously filled out
        instance = self.instance
        if instance:
            kyc_fields = ['kyc_email', 'phone_number', 'address', 'city', 
                         'country', 'employer', 'salary_range']
            
            # Check if any of the required KYC fields have values
            has_existing_kyc = any(
                getattr(instance, field) 
                for field in kyc_fields
            )

            if has_existing_kyc:
                raise serializers.ValidationError(
                    "KYC information has already been submitted and cannot be updated."
                )


        kyc_email = attrs.get('kyc_email')
        confirm_email = attrs.get('confirm_email')
        phone_number = attrs.get('phone_number')
        confirm_phone_number = attrs.get('confirm_phone_number')

        # Email validation logic
        if kyc_email and not confirm_email:
            raise serializers.ValidationError({"confirm_email": "As you edit the KYC Email field, you must also provide the confirmation Email."})

        if confirm_email and not kyc_email:
            raise serializers.ValidationError({"kyc_email": "As you edit the Confirm KYC Email field, you must also provide the Email Field."})

        if kyc_email and confirm_email and kyc_email != confirm_email:
            raise serializers.ValidationError({"kyc_email": "KYC emails do not match."})

        # Phone number validation logic
        if phone_number and not confirm_phone_number:
            raise serializers.ValidationError({"confirm_phone_number": "As you edit the phone number, you must also provide the confirmation phone number."})

        if confirm_phone_number and not phone_number:
            raise serializers.ValidationError({"phone_number": "As you edit the confirmation phone number, you must also provide the phone number."})

        if phone_number and confirm_phone_number and phone_number != confirm_phone_number:
            raise serializers.ValidationError({"phone_number": "KYC phone numbers do not match."})

        return attrs

    def update(self, instance, validated_data):
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.kyc_email = validated_data.get('kyc_email', instance.kyc_email)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.address = validated_data.get('address', instance.address)
        instance.city = validated_data.get('city', instance.city)
        # instance.proof_of_salary = validated_data.get('proof_of_salary', instance.proof_of_salary)
        instance.country = validated_data.get('country', instance.country)
        instance.employer = validated_data.get('employer', instance.employer)
        instance.salary_range = validated_data.get('salary_range', instance.salary_range)
        instance.terms_agreed = validated_data.get('terms_agreed', instance.terms_agreed)

        instance.save()
        return instance

class EmployerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        fields = ['id', 'name', 'industry', 'sector']

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name']

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', 'country']

class SalaryRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryRange
        fields = ['id', 'salary_range', 'currency']


class KYCPatchUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = [
            'kyc_email', 'phone_number', 
            'address', 'city', 'country', 
            'employer', 'salary_range'
        ]
        extra_kwargs = {
            'kyc_email': {'required': False},
            'phone_number': {'required': False},
            'address': {'required': False},
            'city': {'required': False},
            'country': {'required': False},
            'employer': {'required': False},
            'salary_range': {'required': False},
        }

    def update(self, instance, validated_data):
        instance.kyc_email = validated_data.get('kyc_email', instance.kyc_email)
        instance.phone_number = validated_data.get('kyc_phone_number', instance.kyc_phone_number)
        instance.address = validated_data.get('address', instance.address)
        instance.city = validated_data.get('city', instance.city)
        instance.country = validated_data.get('country', instance.country)
        instance.employer = validated_data.get('employer', instance.employer)
        instance.salary_range = validated_data.get('salary_range', instance.salary_range)

        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
        else:
            raise serializers.ValidationError('Email and password are required.')

        data['user'] = user  
        return data


class TwoFASerializer(serializers.Serializer):
    two_fa_code = serializers.CharField()
    user_id = serializers.UUIDField()

    def validate(self, data):
        two_fa_code = data.get('two_fa_code')
        user_id = data.get('user_id')

        try:
            user = UserProfile.objects.get(userId=user_id)
        except UserProfile.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")

        if not user.two_fa_code or not user.two_fa_code_expires:
            raise serializers.ValidationError('No active 2FA code found. Please request a new code.')
        
        if timezone.now() > user.two_fa_code_expires:
            # Clear expired code
            user.two_fa_code = None
            user.two_fa_code_identifier = None
            user.two_fa_code_expires = None
            user.save()
            raise serializers.ValidationError('2FA code has expired. Please request a new code.')

        if user.two_fa_code != two_fa_code:
            raise serializers.ValidationError('Invalid 2FA code.')

        data['user'] = user
        return data

class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = UserProfile.objects.get(email=value)
        except UserProfile.DoesNotExist:
            raise serializers.ValidationError("No user is associated with this email.")
        return value

    def save(self):
        email = self.validated_data['email']
        user = UserProfile.objects.get(email=email)
        
        # Invalidate all existing reset links for this user
        PasswordReset.objects.filter(user=user).update(expires_at=timezone.now())

        # Create a new reset link with 5-minute expiration
        reset_code = secrets.token_urlsafe(32)
        expiration_time = timezone.now() + timedelta(minutes=5)

        password_reset = PasswordReset.objects.create(
            user=user,
            reset_code=reset_code,
            expires_at=expiration_time
        )

        # Build reset URL
        reset_url = f"{settings.FRONTEND_URL}/thrifto/reset-password/{reset_code}/"

        # Send email
        log_and_send_email(
            user=user,
            action_type='PASSWORD_RESET',
            reset_url=reset_url
        )

        return {'message': "Password reset link sent successfully.", 'user': user}


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")
        return data

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        refresh = attrs.get('refresh')

        if not refresh:
            raise serializers.ValidationError("Refresh token is required.")

        return attrs