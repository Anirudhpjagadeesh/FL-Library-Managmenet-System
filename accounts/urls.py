from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, UserViewSet, MeView

# DRF router for Users API
router = DefaultRouter()
router.register('users', UserViewSet, basename='users')

# Combine router URLs with register path
urlpatterns = [
    path('', include(router.urls)),        # /api/auth/users/ → Users API
    path('register/', RegisterView.as_view()),  # /api/auth/register/ → Register
    path('me/', MeView.as_view()),  # /api/auth/me/ → Current user info
]
