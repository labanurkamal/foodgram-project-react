from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import (TagViewSet, SubcribeViewSet, FoodUserViewSet,
                    RecipeViewSet, IngredientViewSet, FavoriteViewSet,
                    ShoppingCartViewSet)

router_v1 = SimpleRouter()
router_v1.register('users', FoodUserViewSet, basename='user')
router_v1.register('tags', TagViewSet, basename='tag')
router_v1.register('recipes', RecipeViewSet, basename='recipe')
router_v1.register('ingredients', IngredientViewSet, basename='ingredient')

create_destroy = {'post': 'create', 'delete': 'destroy'}

recipes = [
    path('<int:id>/favorite/',
         FavoriteViewSet.as_view(create_destroy), name='favorite'),
    path('<int:id>/shopping_cart/',
         ShoppingCartViewSet.as_view(create_destroy), name='shopping_cart'),
]

urlpatterns = [
    path('', include(router_v1.urls)),
    path('recipes/', include(recipes)),
    path('users/<int:id>/subscribe/',
         SubcribeViewSet.as_view(create_destroy), name='subscribe'),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
