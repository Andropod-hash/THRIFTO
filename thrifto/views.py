import random
from django.conf import settings

from django.contrib.auth import login
from rest_framework import generics, status
from django.core.mail import send_mail

from rest_framework.response import Response
from django.core.exceptions import ValidationError


from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from django.utils.decorators import method_decorator

from rest_framework.permissions import AllowAny
from .models import UserProfile, Device, Group
from datetime import datetime, timedelta
from rest_framework.exceptions import ParseError

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt


from rest_framework.authtoken.models import Token
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from .serializers import UserRegistrationSerializer, KYCSerializer, LoginSerializer, TwoFASerializer, CreateGroupSerializer, AddMemberSerializer, KYCPatchUpdateSerializer

class UserRegistrationView(generics.CreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=UserRegistrationSerializer)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "user": UserRegistrationSerializer(user).data,
                "message": "User registered successfully."
            },
            status=status.HTTP_201_CREATED
        ) 
        
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

    @swagger_auto_schema(request_body=KYCSerializer)
    def put(self, request, *args, **kwargs):
        """
        Handle updates for KYC registration.
        """
        instance = self.get_object()
        serializer = KYCSerializer(instance, data=request.data)

        if serializer.is_valid():
            serializer.save()
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
        ip = x_forwarded_for.split(',')[0]
        print(client_ip)
    else:
        ip = request.META.get('REMOTE_ADDR')
        print('error')
    return ip    


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']  

        if user.two_fa_code and not user.two_fa_verified:
            return Response(
                {"message": "2FA verification required. Please enter the 2FA code sent to your email."},
                status=status.HTTP_403_FORBIDDEN
            )

        request_ip = get_client_ip(request)

        device, created = Device.objects.get_or_create(
            user=user,
            device_identifier=request_ip,
        )

        if created:
            self.send_2fa_code(user)
            return Response({
                "message": "2FA code sent to your email.",
                "user_id": user.id  
            }, status=status.HTTP_200_OK)

        login(request, user)
        return Response({"message": "Logged in successfully."}, status=status.HTTP_200_OK)

    def send_2fa_code(self, user):
        """Generate and send a 2FA code to the user's email."""
        user.two_fa_code = f"{random.randint(100000, 999999)}"
        user.two_fa_code_expires = timezone.now() + timedelta(minutes=5)
        user.two_fa_verified = False  
        user.save()

        send_mail(
            'Your 2FA Code',
            f'Your two-factor authentication code is {user.two_fa_code}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

class TwoFAValidationView(APIView):

    permission_classes = [IsAuthenticated]  

    @swagger_auto_schema(request_body=TwoFASerializer)
    def post(self, request, *args, **kwargs):
        serializer = TwoFASerializer(data=request.data)

        if not serializer.is_valid():
            print(f"Serializer errors: {serializer.errors}") 
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']

        user.two_fa_verified = True
        user.two_fa_code = None  
        user.two_fa_code_expires = None  
        user.save()

        request.user.backend = 'thrifto.backends.EmailBackend'  
        login(request, user, backend=request.user.backend)

        return Response({"message": "2FA verified successfully. Logged in."}, status=status.HTTP_200_OK)
class KYCUpdate(APIView):
    """
    View for updating KYC information, accessible only to authenticated users.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=KYCPatchUpdateSerializer)
    def patch(self, request, *args, **kwargs):
        instance = request.user  
        if 'kyc_email' in request.data:
            request.data['email_confirmed'] = True

        serializer = KYCPatchUpdateSerializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "KYC information updated successfully."}, status=status.HTTP_200_OK)


class CreateGroupView(APIView):
    """
    View for creating a group, accessible only to authenticated users.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=CreateGroupSerializer)
    def post(self, request, *args, **kwargs):
        serializer = CreateGroupSerializer(data=request.data, context={'request': request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        group = serializer.save()

        if group.members.count() >= 6:
            return Response({"message": "Cannot add more than 6 members to the group."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "Group created successfully.",
            "group_id": group.id,
            "group_name": group.name,
            "admin": group.admin.username
        }, status=status.HTTP_201_CREATED)

class AddMemberView(APIView):
    serializer_class = AddMemberSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            group_id = self.request.data.get('group_id')
            return Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            raise NotFound(detail="Group not found.", code=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(request_body=AddMemberSerializer)
    def patch(self, request, *args, **kwargs):
        try:
            if not isinstance(request.data, dict):
                return Response({"message": "Invalid JSON format."}, status=status.HTTP_400_BAD_REQUEST)

            group = self.get_object()

            if group.admin != request.user:
                return Response({"message": "Only the admin can add members."}, status=status.HTTP_403_FORBIDDEN)

            current_member_count = group.members.count()

            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)

            member_ids = serializer.validated_data['member_id']

            if not isinstance(member_ids, list):
                return Response({"message": "Member IDs should be a list."}, status=status.HTTP_400_BAD_REQUEST)
            if len(member_ids) > 2:
                return Response({"message": "You can only add up to 2 members at a time."}, status=status.HTTP_400_BAD_REQUEST)

            available_slots = 6 - current_member_count
            if available_slots <= 0:
                return Response({
                    "message": "Cannot add more members. Group already has 6 members."
                }, status=status.HTTP_400_BAD_REQUEST)

            if len(member_ids) > available_slots:
                return Response({
                    "message": f"Cannot add more than {available_slots} member(s). Group can only have a maximum of 6 members."
                }, status=status.HTTP_400_BAD_REQUEST)

            new_members = []
            for member_id in member_ids:
                if group.members.filter(id=member_id).exists():
                    return Response({"message": f"User with ID {member_id} is already a member of the group."}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    member = UserProfile.objects.get(id=member_id)
                    new_members.append(member)
                except UserProfile.DoesNotExist:
                    return Response({"message": f"User with ID {member_id} does not exist."}, status=status.HTTP_404_NOT_FOUND)

            group.members.add(*new_members)

            return Response({
                "message": f"Successfully added {len(new_members)} new member(s) to the group."
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"message": "Invalid data provided: " + str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
