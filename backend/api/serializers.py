import base64

from django.db.models import F
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient,
    ShoppingCart, Subscription, Tag
)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Поле сериализатора для обработки изображений в формате base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class AuthorSerializer(UserSerializer):
    """Сериализатор для пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = ('id', 'email', *User.REQUIRED_FIELDS, 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and obj.subscriptions.exists()
        )


class SubscriptionsSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ['subcripe', 'recipes', 'recipes_count']

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes_list = obj.subcripe.recipes.all()
        if recipes_limit and recipes_limit.isdigit():
            recipes_list = recipes_list[:int(recipes_limit)]

        return recipes_list

    def get_recipes_count(self, obj):
        return self.get_recipes(obj).count()

    def to_representation(self, instance):
        representation = dict(AuthorSerializer(
            instance.subcripe,
            context={'request': self.context.get('request')}).data
        )
        representation['recipes'] = RecipeShortSerializer(
            self.get_recipes(instance), many=True).data
        representation['recipes_count'] = self.get_recipes_count(instance)
        return representation


class SubscripeSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки."""
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    subcripe = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False
    )

    class Meta:
        model = Subscription
        fields = ['author', 'subcripe']
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('author', 'subcripe'),
                message='Вы уже подписаны на этого пользователя.'
            )
        ]

    def validate_subcripe(self, subcripe):
        """Проверяет, что пользователь не может подписаться на самого себя."""
        if subcripe == self.context['request'].user:
            raise serializers.ValidationError(
                {'errors': 'Вы не может подписаться на самого себя.'})
        return subcripe

    def to_representation(self, instance):
        return SubscriptionsSerializer(
            instance, context={'request': self.context.get('request')}).data


class IngredientReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для промежуточной модели рецепта и ингредиента."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткий сериализатор рецепта."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    author = AuthorSerializer(required=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and obj.favorites.exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and obj.shopcarts.exists()
        )

    def get_ingredients(self, obj):
        ingredients = obj.ingredients.values(
            'id', 'name', 'measurement_unit',
            amount=F('recipeingredient__amount'))
        return ingredients


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания рецепта."""
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    ingredients = IngredientWriteSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def validate(self, attrs):
        """Проверка наличие обязательных полей и их заполненность рецепта."""
        request = self.context.get('request')

        if request.method in ('POST', 'PATCH'):
            for field in ('tags', 'ingredients'):
                if not attrs.get(field):
                    raise serializers.ValidationError(
                        f'Поле {field} не может быть пустой ')

                if len(set(attrs['tags'])) != len(attrs.get('tags', [])):
                    raise serializers.ValidationError(
                        "Был указан повторяющиеся тег")

                ingredient = [i['id'] for i in attrs.get('ingredients', [])]
                if len(set(ingredient)) != len(ingredient):
                    raise serializers.ValidationError(
                        "Был указан повторяющиеся ингредиенты")
        return attrs

    @staticmethod
    def ingredient_bulk_create(recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient.get('amount')
            )
            for ingredient in ingredients
        )

    def create(self, validated_data):
        """Создание нового рецепта."""
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        self.ingredient_bulk_create(recipe=recipe, ingredients=ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновление существующего рецепта."""
        ingredients = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags', [])
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.ingredient_bulk_create(
            recipe=instance,
            ingredients=ingredients
        )

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Преобразование объекта в представление."""
        return RecipeReadSerializer(
            instance, context={'request': self.context.get('request')}).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного."""
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        required=False
    )

    class Meta:
        model = Favorite
        fields = ('author', 'recipe')
        read_only_fields = ('id', 'author', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('author', 'recipe'),
                message='Рецепт уже есть в избранного.'
            )
        ]

    def to_representation(self, instance):
        return RecipeShortSerializer(instance.recipe).data


class ShoppingCartSerializer(FavoriteSerializer):
    """Сериализатор для покупки."""

    class Meta(FavoriteSerializer.Meta):
        model = ShoppingCart
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('author', 'recipe'),
                message='Рецепт уже есть в список покупок.'
            )
        ]
