from rest_framework import serializers
from django.utils import timezone
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import UserProfile, Device,  Group
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate


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
    class Meta:
        model = UserProfile
        fields = [
            'full_name',
            'kyc_email', 'confirm_kyc_email', 
            'kyc_phone_number', 'confirm_kyc_phone_number', 
            'address', 'city', 'country', 'employer', 'salary_range',
            'email_confirmed', 'phone_number_confirmed', 'terms_agreed', 'kyc_confirmed'
        ]

        extra_kwargs = {
            'kyc_email': {'required': True, 'error_messages': {'required': 'KYC email is required.'}},
            'confirm_kyc_email': {'required': True, 'error_messages': {'required': 'Confirmation KYC email is required.'}},
            'kyc_phone_number': {'required': True, 'error_messages': {'required': 'KYC phone number is required.'}},
            'confirm_kyc_phone_number': {'required': True, 'error_messages': {'required': 'Confirmation KYC phone number is required.'}},
            'address': {'required': True, 'error_messages': {'required': 'Address is required.'}},
            'city': {'required': True, 'error_messages': {'required': 'City is required.'}},
            'country': {'required': True, 'error_messages': {'required': 'Country is required.'}},
            'employer': {'required': True, 'error_messages': {'required': 'Employer information is required.'}},
            'salary_range': {'required': True, 'error_messages': {'required': 'Salary range is required.'}},
            'terms_agreed': {'required': True, 'error_messages': {'required': 'You must agree to the terms.'}},
        }

    def validate(self, attrs):
        kyc_email = attrs.get('kyc_email')
        confirm_kyc_email = attrs.get('confirm_kyc_email')
        kyc_phone_number = attrs.get('kyc_phone_number')
        confirm_kyc_phone_number = attrs.get('confirm_kyc_phone_number')

      
        if self.instance and self.instance.kyc_confirmed:
            raise serializers.ValidationError(
                'KYC has already been confirmed. Please use the KYC update endpoint to modify your details.'
            )


        if kyc_email and not confirm_kyc_email:
            raise serializers.ValidationError({"confirm_kyc_email" : "As you edit the Kyc Email field, you must also provide the confirmation Email."})

        if confirm_kyc_email and not kyc_email:
            raise serializers.ValidationError({"kyc_email" : "As you edit the Confirm Kyc Email field, you must also provide the Email Field."})

        if kyc_email and confirm_kyc_email and kyc_email != confirm_kyc_email:
            raise serializers.ValidationError({"kyc_email": "KYC emails do not match."})

        if kyc_phone_number and not confirm_kyc_phone_number:
            raise serializers.ValidationError({"confirm_kyc_phone_number": "As you edit the phone number, you must also provide the confirmation phone number."})
        
        if confirm_kyc_phone_number and not kyc_phone_number:
            raise serializers.ValidationError({"kyc_phone_number": "As you edit the confirmation phone number, you must also provide the phone number."})

        if kyc_phone_number and confirm_kyc_phone_number and kyc_phone_number != confirm_kyc_phone_number:
            raise serializers.ValidationError({"kyc_phone_number": "KYC phone numbers do not match."})

        return attrs

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.email = validated_data.get('email', instance.email)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)

        instance.kyc_email = validated_data.get('kyc_email', instance.kyc_email)
        instance.confirm_kyc_email = validated_data.get('confirm_kyc_email', instance.confirm_kyc_email)
        instance.kyc_phone_number = validated_data.get('kyc_phone_number', instance.kyc_phone_number)
        instance.confirm_kyc_phone_number = validated_data.get('confirm_kyc_phone_number', instance.confirm_kyc_phone_number)

        instance.address = validated_data.get('address', instance.address)
        instance.city = validated_data.get('city', instance.city)
        instance.country = validated_data.get('country', instance.country)
        instance.employer = validated_data.get('employer', instance.employer)
        instance.salary_range = validated_data.get('salary_range', instance.salary_range)

        instance.email_confirmed = validated_data.get('email_confirmed', instance.email_confirmed)
        instance.phone_number_confirmed = validated_data.get('phone_number_confirmed', instance.phone_number_confirmed)
        instance.terms_agreed = validated_data.get('terms_agreed', instance.terms_agreed)

        instance.save()
        return instance

class KYCPatchUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'kyc_email', 'kyc_phone_number', 
            'address', 'city', 'country', 
            'employer', 'salary_range'
        ]
        extra_kwargs = {
            'kyc_email': {'required': False},
            'kyc_phone_number': {'required': False},
            'address': {'required': False},
            'city': {'required': False},
            'country': {'required': False},
            'employer': {'required': False},
            'salary_range': {'required': False},
        }

    def update(self, instance, validated_data):
        instance.kyc_email = validated_data.get('kyc_email', instance.kyc_email)
        instance.kyc_phone_number = validated_data.get('kyc_phone_number', instance.kyc_phone_number)
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
    user_id = serializers.IntegerField()

    def validate(self, data):
        two_fa_code = data.get('two_fa_code')
        user_id = data.get('user_id')

        try:
            user = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")

        print(f"Debug Info: User's 2FA code: {user.two_fa_code}, Expires at: {user.two_fa_code_expires}")
        print(f"Debug Info: Current time: {timezone.now()}")

        # To Validate the 2FA code and its expiration
        if user.two_fa_code != two_fa_code:
            raise serializers.ValidationError('Invalid 2FA code.')
        
        if timezone.now() > user.two_fa_code_expires:
            raise serializers.ValidationError('2FA code has expired.')

        data['user'] = user 
        return data

class CreateGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name', 'members']
        extra_kwargs = {
            'members': {'required': False}  # Members are optional
        }

    def create(self, validated_data):

        members = validated_data.pop('members', [])

        group = Group(**validated_data)
        
        # Set the admin to the request user
        group.admin = self.context['request'].user

        group.save()
        
        # Add the creator to the group members list
        group.members.add(self.context['request'].user)
        
        # Optionally add other members if provided
        if members:
            group.members.add(*members)

        return group
    

class AddMemberSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()  # Add group_id field
    member_id = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text="List of member IDs to add to the group (maximum of 2 members)."
    )

    def validate_member_id(self, value):
        # Ensure the list contains no more than 2 member IDs
        if len(value) > 2:
            raise serializers.ValidationError("You can only add up to 2 members at a time.")
        for member_id in value:
            try:
                user = UserProfile.objects.get(id=member_id)
            except UserProfile.DoesNotExist:
                raise serializers.ValidationError(f"User with ID {member_id} does not exist.")
        return value

    def validate_group_id(self, value):
        # Check if the group exists
        try:
            group = Group.objects.get(id=value)
        except Group.DoesNotExist:
            raise serializers.ValidationError("Group does not exist.")
        return value
