"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="My API",  # Replace with the title of your API
        default_version='v1',  # The version of your API
        description="This is the API for my application",  # A brief description of your API
        terms_of_service="https://www.myapi.com/terms/",  # Link to the terms of service for your API
        contact=openapi.Contact(email="contact@myapi.com"),  # Your contact email
        license=openapi.License(name="MIT License"),  # The license for your API
    ),
    public=True,  # Set to True if your API is public
    permission_classes=(permissions.AllowAny,),  # The permission classes for accessing the schema view
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('thrifto/', include('thrifto.urls')),  
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),  # URL to access the Swagger UI
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]