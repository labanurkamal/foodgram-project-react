from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import (
    Tag, Ingredient, Recipe, Favorite,
    ShoppingCart, Subscription
)

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Администрирование пользователей."""
    list_display = ('id', 'username', 'email', 'first_name', 'last_name')
    list_filter = ('username', 'email')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Администрирование тегов."""
    list_display = ('name', 'color', 'slug')
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Администрирование ингредиентов."""
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Администрирование рецептов."""
    list_display = ('name', 'author')
    list_filter = ('author', 'name', 'tags')
    search_fields = ('name',)

    def get_favorites_count(self, obj):
        return obj.favorites.count()
    get_favorites_count.short_description = 'Favorites Count'

    readonly_fields = ('get_favorites_count',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Администрирование избранных рецептов."""
    list_display = ('author', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Администрирование списка покупок."""
    list_display = ('author', 'recipe')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Администрирование подписок."""
    list_display = ('author', 'subcripe')
