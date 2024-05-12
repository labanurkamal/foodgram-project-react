from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FoodUserViewSet, IngredientViewSet, RecipeViewSet, TagViewSet)

router_v1 = DefaultRouter()
router_v1.register('users', FoodUserViewSet, basename='user')
router_v1.register('tags', TagViewSet, basename='tag')
router_v1.register('recipes', RecipeViewSet, basename='recipe')
router_v1.register('ingredients', IngredientViewSet, basename='ingredient')


urlpatterns = [
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
