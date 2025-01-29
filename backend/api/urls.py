from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import *


app_name = 'api'

router = DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')
# router.register('users', CustomUserViewSet, basename='users')


urlpatterns = [
    path('', include(router.urls), name='api-root'),
    re_path('auth/', include('djoser.urls.authtoken')),
]