from django.urls import path
from .views import UserRegistrationView, KYCRegistrationView, LoginView, TwoFAValidationView, KYCUpdate, CreateGroupView,  AddMemberView

print(f"Type of TwoFAValidationView: {type(TwoFAValidationView)}")  

urlpatterns = [
    path('api/register/', UserRegistrationView.as_view(), name='user-register'),
    path('api/kyc/', KYCRegistrationView.as_view(), name='kyc-register'),
    path('api/login/', LoginView.as_view(), name='login'),  
    path('api/2FAlogin/', TwoFAValidationView.as_view(), name='2FA'),
    path('kyc/update/', KYCUpdate.as_view(), name='kyc-update'),
    path('group/create/', CreateGroupView.as_view(), name='kyc-update'),
    path('group/update/<int:pk>/', AddMemberView.as_view(), name='kyc-update'),
]
