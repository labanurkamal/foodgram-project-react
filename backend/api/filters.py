from django_filters import AllValuesMultipleFilter, rest_framework as filters

from recipes.models import Recipe


class RecipeFilterSet(filters.FilterSet):
    """
    Фильтр для рецептов.

    Позволяет фильтровать рецепты по различным критериям, включая теги,
    наличие в избранном и наличие в списке покупок.
    """
    tags = AllValuesMultipleFilter(field_name='tags__slug', label='Tags')
    is_favorited = filters.BooleanFilter(method='filter_favorite')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def filter_favorite(self, queryset, name, bool_val):
        """Фильтрует рецепты наличию в избранном для текущего пользователя."""
        author = self.request.user
        if bool_val and author.is_authenticated:
            queryset = queryset.filter(favorites__author=author)
        return queryset

    def filter_shopping_cart(self, queryset, name, bool_val):
        """Фильтрует рецепты наличию в покупок для текущего пользователя."""
        author = self.request.user
        if bool_val and author.is_authenticated:
            queryset = queryset.filter(shopcarts__author=author)
        return queryset
