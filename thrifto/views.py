import random
import uuid
from django.conf import settings

from django.contrib.auth import login
from rest_framework import generics, status, viewsets
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from drf_yasg import openapi
from django.http import HttpResponseRedirect
from rest_framework_simplejwt.tokens import RefreshToken
import random
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from rest_framework.response import Response
from Notifications.utilis import log_and_send_email
from django.core.exceptions import ValidationError


from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from django.utils.decorators import method_decorator

from rest_framework.permissions import AllowAny
from .models import UserProfile, Device, Group, City, Country, Employer, SalaryRange, PasswordReset
from datetime import datetime, timedelta
from rest_framework.exceptions import ParseError

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt  # 
from rest_framework.decorators import api_view, permission_classes,action


from rest_framework.authtoken.models import Token
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from .serializers import UserRegistrationSerializer, ResetPasswordSerializer, ForgetPasswordSerializer, LogoutSerializer, KYCSerializer, LoginSerializer, SalaryRangeSerializer, EmployerSerializer, TwoFASerializer, KYCPatchUpdateSerializer, CountrySerializer, CitySerializer


class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            log_and_send_email(user, 'SIGNUP')

            return Response(
                {
                    "user": UserRegistrationSerializer(user).data,
                    "message": "User registered successfully."
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
           
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
 
class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

    def list(self, request, *args, **kwargs):
        """List all countries."""
        return super().list(request, *args, **kwargs)

class SalaryRangeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SalaryRange.objects.all()
    serializer_class = SalaryRangeSerializer

    def list(self, request, *args, **kwargs):
        """List all SalaryRange."""
        return super().list(request, *args, **kwargs)

class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer

    @action(detail=False)
    def by_country(self, request):
        country_id = request.query_params.get('country_id')
        if country_id:
            cities = City.objects.filter(country_id=country_id)
            serializer = self.get_serializer(cities, many=True)
            return Response(serializer.data)
        return Response(status=status.HTTP_400_BAD_REQUEST)

class EmployerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Employer.objects.all()
    serializer_class = EmployerSerializer

    def list(self, request, *args, **kwargs):
        """ List all employers."""
        return super().list(request, *args, **kwargs)

class KYCRegistrationView(APIView):
    """
    View for KYC registration, accessible only to authenticated users.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Get the user object based on the logged-in user.
        """
        user = self.request.user
        return UserProfile.objects.get(email=user.email)

    def put(self, request, *args, **kwargs):
        """
        Handle updates for KYC registration.
        """
        instance = self.get_object()
        serializer = KYCSerializer(instance, data=request.data)

        if serializer.is_valid():
            serializer.save()

            log_and_send_email(request.user, 'KYC_CONFIRMED')  
            
            return Response(
                {
                    "kyc": serializer.data,
                    "message": "KYC details updated successfully."
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def get_client_ip(request):
    """Get the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        request_ip = get_client_ip(request)
        
        device, created = Device.objects.get_or_create(
            user=user,
            device_identifier=request_ip,
        )

        # Always send a new 2FA code for unverified devices
        if created or not device.is_verified:
            self.send_2fa_code(user)
            return Response({
                "message": "2FA code sent to your email.",
                "user_id": str(user.userId)
            }, status=status.HTTP_200_OK)

        # For verified devices, proceed with normal login
        refresh = RefreshToken.for_user(user)
        ip_address = get_client_ip(request)
        log_and_send_email(user, 'LOGIN', ip_address=ip_address)

        return Response({
            "message": "Logged in successfully.",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)

    def send_2fa_code(self, user):  
        """
        Send 2FA code to the user who just signed up
        
        """
        try:
            # Generate new code
            new_code = f"{random.randint(100000, 999999)}"
            
            # Store the code and expiry time with the user
            user.two_fa_code = new_code
            user.two_fa_code_expires = timezone.now() + timedelta(minutes=5)
            user.two_fa_verified = False
            user.save()

            # Create email content
            html_message = f"""
            <html>
                <body>
                    <h2>Welcome {user.username}!</h2>
                    <h3>Your Verification Code</h3>
                    <p>Your verification code is: <strong>{new_code}</strong></p>
                    <p>This code will expire in 5 minutes.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                </body>
            </html>
            """
            
            # Create plain text version
            plain_message = strip_tags(html_message)
            
            # Create email to send to user's email address
            email = EmailMessage(
                subject='Your Verification Code',
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
                reply_to=[settings.DEFAULT_FROM_EMAIL]
            )
            
            # Set content type to HTML
            email.content_subtype = "html"
            
            # Send email
            email.send(fail_silently=False)
            
            return True, f"2FA code sent successfully to {user.email}"
            
        except Exception as e:
            return False, f"Failed to send 2FA code: {str(e)}"


class TwoFAValidationView(APIView):

    def post(self, request, *args, **kwargs):
        serializer = TwoFASerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        device = Device.objects.get(
            user=user,
            device_identifier=get_client_ip(request)
        )
        
        # Mark device as verified
        device.is_verified = True
        device.save()

        # Clear 2FA code after successful verification
        user.two_fa_verified = True
        user.two_fa_code = None
        user.two_fa_code_identifier = None
        user.two_fa_code_expires = None
        user.save()

        # Generate JWT token after 2FA verification
        refresh = RefreshToken.for_user(user)
        ip_address = get_client_ip(request)
        log_and_send_email(user, 'LOGIN', ip_address=ip_address)

        return Response({
            "message": "2FA verified successfully. Logged in.",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)

class KYCUpdate(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=KYCPatchUpdateSerializer)
    def patch(self, request, *args, **kwargs):
        instance = request.user  
        if 'kyc_email' in request.data:
            request.data['email_confirmed'] = True

        serializer = KYCPatchUpdateSerializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"KYC update successful for user: {user.email}")
            
            # Send the KYC confirmation email
            success = log_and_send_email(user, 'KYC_CONFIRMED')
            
            return Response({
                "message": "KYC information updated successfully.",
                "email_sent": success
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)

        if serializer.is_valid():
            try:
                refresh_token = serializer.validated_data['refresh']
                
                # Blacklist the refresh token
                token = RefreshToken(refresh_token)
                token.blacklist()

                return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgetPasswordView(APIView):
    def post(self, request):
        serializer = ForgetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response({"message": "Password reset email sent successfully"})
        return Response(serializer.errors, status=400)

class ResetPasswordView(APIView):
    def get(self, request, reset_code):
        try:
            reset_request = PasswordReset.objects.get(reset_code=reset_code)
            if reset_request.expires_at <= timezone.now():
                return Response({"error": "This reset code has expired"}, status=400)
            return Response({"message": "Please enter your new password"})
        except PasswordReset.DoesNotExist:
            return Response({"error": "Invalid reset code"}, status=400)

    def post(self, request, reset_code):
        try:
            reset_request = PasswordReset.objects.get(reset_code=reset_code)
            if reset_request.expires_at <= timezone.now():
                return Response({"error": "This reset code has expired"}, status=400)
        except PasswordReset.DoesNotExist:
            return Response({"error": "Invalid reset code"}, status=400)

        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = reset_request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Invalidate all reset codes for this user
            PasswordReset.objects.filter(user=user).delete()
            
            return Response({"message": "Password reset successfully"})
        return Response(serializer.errors, status=400)