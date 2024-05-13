from django.db.models import F
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from djoser.views import UserViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, validators, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from . import mixins, serializers
from .filters import RecipeFilterSet
from .paginations import PageLimitPagination
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from module import scripts
from recipes.models import Ingredient, Recipe, Tag


User = get_user_model()


class FoodUserViewSet(UserViewSet):
    """ViewSet для управления пользователями."""
    queryset = User.objects.all()
    serializer_class = serializers.AuthorSerializer
    pagination_class = LimitOffsetPagination

    def get_permissions(self):
        if self.action in ['retrieve', 'list']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_serializer(self, *args, **kwargs):
        context = {'request': self.request}
        if self.action in ('list', 'retrieve', 'me'):
            return serializers.AuthorSerializer(
                *args, **kwargs, context=context)
        elif self.action == 'subscribe':
            return serializers.SubscripeSerializer(
                *args, **kwargs, context=context)
        elif self.action == 'subscriptions':
            return serializers.SubscriptionsSerializer(
                *args, **kwargs, context=context)
        return super().get_serializer(*args, **kwargs)

    @action(methods=['post'],
            detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data={'subcripe': self.get_object().id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def subscribe_destroy(self, request, *args, **kwargs):
        instance, _ = request.user.subscriptions.filter(
            subcripe=self.get_object()
        ).delete()
        if not instance:
            raise validators.ValidationError(
                {'errors': 'Этот пользватель не добавлен в подписку.'})
        return Response(status=status.HTTP_204_NO_CONTENT)

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
    queryset = Recipe.objects.prefetch_related('tags', 'ingredients').all()
    serializer_class = serializers.RecipeCreateSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_class = RecipeFilterSet
    pagination_class = PageLimitPagination
    permission_classes = [IsAuthorOrReadOnly | IsAdminOrReadOnly]

    def get_serializer(self, *args, **kwargs):
        if self.action in ('list', 'retrieve'):
            return serializers.RecipeReadSerializer(
                *args, **kwargs, context={'request': self.request})
        elif self.action == 'shopping_cart':
            return serializers.ShoppingCartSerializer(*args, **kwargs)
        elif self.action == 'favorite':
            return serializers.FavoriteSerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)

    @action(methods=['post'],
            detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, *args, **kwargs):
        return self.perform_create_response(*args, **kwargs)

    @shopping_cart.mapping.delete
    def destroy_shopping_cart(self, request, *args, **kwargs):
        instance, _ = request.user.shopcarts.filter(
            recipe=self.get_object()
        ).delete()
        if not instance:
            raise validators.ValidationError(
                {'errors': 'Этот рецепт не добавлен в список покупок'})
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'],
            detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, *args, **kwargs):
        return self.perform_create_response(*args, **kwargs)

    @favorite.mapping.delete
    def destroy_favorite(self, request, *args, **kwargs):
        instance, _ = request.user.favorites.filter(
            recipe=self.get_object()
        ).delete()
        if not instance:
            raise validators.ValidationError(
                {'errors': 'Этот рецепт не добавлен в избранный'})
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False)
    def download_shopping_cart(self, request, *args, **kwargs):
        """Загрузка списка покупок в виде текстового файла."""
        ingredient_list = []
        for cart in request.user.shopcarts.all():
            ingredient = cart.recipe.ingredients.values(
                'id',
                'name',
                'measurement_unit',
                amount=F('recipeingredient__amount')).all()
            ingredient_list.extend(ingredient.values())

        filename = scripts.txt_export(
            scripts.combine_ingredients(ingredient_list))

        with open(filename, 'rb') as file:
            response = HttpResponse(file.read(), content_type='text/plain')

        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def perform_create_response(self, *args, **kwargs):
        """
        Выполняет создание объекта и возвращает ответ.
        Создает объект рецепта с использованием данных, полученных из запроса.
        """
        serializer = self.get_serializer(
            context={'request': self.request},
            data={'recipe': kwargs['pk']}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class IngredientViewSet(mixins.IngredientTagViewSet):
    """ViewSet для управления ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientReadSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)


class TagViewSet(mixins.IngredientTagViewSet):
    """ViewSet для управления тегами."""
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
