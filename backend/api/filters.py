from django_filters import rest_framework

from recipes.models import Recipe, Tag


class RecipeFilterSet(rest_framework.FilterSet):
    tags = rest_framework.ModelMultipleChoiceFilter(field_name='tags__slug',
                                                    to_field_name='slug',
                                                    queryset=Tag.objects.all())
    is_favorited = rest_framework.BooleanFilter(method='filter_favorite')
    is_in_shopping_cart = rest_framework.BooleanFilter(
        method='filter_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def filter_favorite(self, queryset, name, bool_val):
        author = self.request.user
        if bool_val and author.is_authenticated:
            queryset = queryset.filter(favorites__author=author)
        return queryset

    def filter_shopping_cart(self, queryset, name, bool_val):
        author = self.request.user
        if bool_val and author.is_authenticated:
            queryset = queryset.filter(shopcarts__author=author)
        return queryset
