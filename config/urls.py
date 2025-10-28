from django.contrib import admin
from django.urls import path, include
from django.urls import re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Library Snippets API",
      default_version='v1',
      description="Library description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="Library contact@snippets.local"),
      license=openapi.License(name="Library BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls', namespace='users')),
    path('api/library/', include('library.urls', namespace='library')),

    # Swagger
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
