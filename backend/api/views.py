from collections import defaultdict

from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import viewsets, validators, permissions, filters
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination

from . import mixins, serializers
from .permissions import IsAuthorOrReadOnly, IsAdminOrReadOnly
from recipes.models import (Recipe, Tag, Ingredient, Subscription,
                            Favorite, ShoppingCart)


User = get_user_model()


class ShoppingCartViewSet(mixins.CreateDestroyViewSets):
    """ViewSet для управления списком покупок."""
    queryset = ShoppingCart.objects.all()
    serializer_class = serializers.ShoppingCartSerializer

    def perform_create(self, serializer):
        recipe = self.get_recipe()
        serializer.save(author=self.request.user, recipe=recipe)

        if not recipe.is_in_shopping_cart:
            self.update_attribute(recipe, 'is_in_shopping_cart', True)

    def perform_destroy(self, instance):
        instance.delete()
        recipe = self.get_recipe()
        if not ShoppingCart.objects.filter(recipe=recipe).exists():
            self.update_attribute(recipe, 'is_in_shopping_cart')


class FavoriteViewSet(mixins.CreateDestroyViewSets):
    """ViewSet для управления избранным."""
    queryset = Favorite.objects.all()
    serializer_class = serializers.FavoriteSerializer

    def perform_create(self, serializer):
        recipe = self.get_recipe()
        serializer.save(author=self.request.user, recipe=recipe)

        if not recipe.is_favorited:
            self.update_attribute(recipe, 'is_favorited', True)

    def perform_destroy(self, instance):
        instance.delete()
        recipe = self.get_recipe()
        if not Favorite.objects.filter(recipe=recipe).exists():
            self.update_attribute(recipe, 'is_favorited')


class SubcribeViewSet(mixins.CreateDestroyViewSets):
    """ViewSet для управления подписками."""
    queryset = Subscription.objects.all()
    serializer_class = serializers.SubscriptionSerializer

    def get_object(self):
        """Получение объекта подписки."""
        queryset = self.filter_queryset(self.get_queryset())
        if self.request.method == 'DELETE':
            if not queryset.filter(author=self.request.user,
                                   subcripe=self.get_subcribe()).exists():
                raise validators.ValidationError(
                    {'errors': 'Этот пользватель не добавлен в подписку.'})
        obj = get_object_or_404(queryset, author=self.request.user,
                                subcripe=self.get_subcribe())
        self.check_object_permissions(self.request, obj)
        return obj

    def get_subcribe(self):
        """Получение пользователя, на которого подписываются."""
        return get_object_or_404(User, pk=self.kwargs.get('id'))

    def get_recipe(self):
        """Получение списка рецептов пользователя."""
        query_recipes = self.get_subcribe().recipes.all()
        recipes_limit = self.request.query_params.get('recipes_limit')
        if recipes_limit:
            query_recipes = query_recipes[:int(recipes_limit)]
        return query_recipes

    def perform_create(self, serializer):
        author = self.request.user
        serializer.save(author=author, subcripe=self.get_subcribe(),
                        recipes=self.get_recipe())
        if not author.is_subscribed:
            self.update_attribute(author, 'is_subscribed', True)

    def perform_destroy(self, instance):
        instance.delete()
        author = self.request.user
        if not author.subscriptions.exists():
            self.update_attribute(author, 'is_subscribed')


class FoodUserViewSet(UserViewSet):
    """ViewSet для управления пользователями."""
    serializer_class = serializers.CustomUserCreateSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        return User.objects.all()

    def get_permissions(self):
        if self.action in ['retrieve', 'list']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_serializer(self, *args, **kwargs):
        if self.action in ('list', 'retrieve', 'me'):
            return serializers.AuthorSerializer(*args, **kwargs)
        elif self.action == 'subscriptions':
            return serializers.SubscriptionSerializer(
                *args, **kwargs, context={'request': self.request})
        return super().get_serializer(*args, **kwargs)

    @action(methods=['get'], detail=False)
    def subscriptions(self, request, *args, **kwargs):
        """Получение списка подписок пользователя."""
        paginator = self.pagination_class()
        serializer = self.get_serializer(
            paginator.paginate_queryset(request.user.subscriptions.all(),
                                        request), many=True)
        return paginator.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для управления рецептами."""
    queryset = Recipe.objects.all()
    serializer_class = serializers.RecipeCreateSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    permission_classes = [IsAuthorOrReadOnly | IsAdminOrReadOnly]
    pagination_class = LimitOffsetPagination
    search_fields = ['name', 'tags__slug', 'author__id']
    filterset_fields = ['is_favorited', 'is_in_shopping_cart',
                        'author', 'tags__slug']

    @staticmethod
    def combine_ingredients(data):
        """Комбинирование ингредиентов."""
        ingredient_totals = defaultdict(int)
        for item in data:
            ingredient_totals[(
                item['name'], item['measurement_unit'])] += item['amount']
        return [{'name': name, 'measurement_unit': unit, 'amount': amount}
                for (name, unit), amount in ingredient_totals.items()]

    def get_queryset(self):
        queryset = self.queryset
        tags = self.request.query_params.getlist('tags')
        if tags:
            query = Q(tags__slug__in=tags)
            queryset = queryset.filter(query).distinct()
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    def txt_export(self, data):
        """Экспорт списка ингредиентов в текстовый файл."""
        filename = 'list_shopping_cart-export.txt'
        measurement_unit = {'кг': (1000, 'г'), 'л': (1000, 'мл')}
        title = "Название | Единица измерения | Количество"

        with open(filename, 'w', encoding='utf-8') as file:
            file.write(f"{title}\n{'-' * len(title)}\n")
            for i, item in enumerate(data, start=1):
                m_unit = measurement_unit.get(item['measurement_unit'])
                if m_unit:
                    item['measurement_unit'] = m_unit[1]
                    item['amount'] *= m_unit[0]
                line = (f"{i}. {item['name']} ({item['measurement_unit']})"
                        f" — {item['amount']}\n")
                file.write(line)
            file.write(f"{'-' * len(title)}")

        with open(filename, 'rb') as file:
            response = HttpResponse(file.read(), content_type='text/plain')

        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(methods=['get'], detail=False)
    def download_shopping_cart(self, request, *args, **kwargs):
        """Загрузка списка покупок в виде текстового файла."""
        ingredients_list = []

        for cart in request.user.shopcarts.all():
            ingredient = cart.recipe.ingredients.all()
            ingredients_list.extend(ingredient.values())

        return self.txt_export(self.combine_ingredients(ingredients_list))


class IngredientViewSet(mixins.IngredientTagViewSet):
    """ViewSet для управления ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)


class TagViewSet(mixins.IngredientTagViewSet):
    """ViewSet для управления тегами."""
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
