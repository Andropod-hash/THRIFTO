from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserRegistrationView, KYCRegistrationView, ResetPasswordView, LoginView, LogoutView, TwoFAValidationView, KYCUpdate, CountryViewSet, CityViewSet, EmployerViewSet, SalaryRangeViewSet, ForgetPasswordView

print(f"Type of TwoFAValidationView: {type(TwoFAValidationView)}")  

router = DefaultRouter()
router.register(r'countries', CountryViewSet)
router.register(r'cities', CityViewSet)
router.register(r'employers', EmployerViewSet)
router.register(r'salary-range', SalaryRangeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api/register/', UserRegistrationView.as_view(), name='user-register'),
    path('api/kyc/', KYCRegistrationView.as_view(), name='kyc-register'),
    path('api/login/', LoginView.as_view(), name='login'),  
    path('api/2FAlogin/', TwoFAValidationView.as_view(), name='2FA'),
    path('kyc/update/', KYCUpdate.as_view(), name='kyc-update'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', ForgetPasswordView.as_view(), name='forgot-password'),
    path('reset-password/<str:reset_code>/', ResetPasswordView.as_view(), name='reset-password'),
  
]
