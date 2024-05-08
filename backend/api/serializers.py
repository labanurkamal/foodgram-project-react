import re
import base64

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import (Tag, Recipe, Ingredient,
                            Subscription, Favorite, ShoppingCart)
from .mixins import MODEL_NAME

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Поле сериализатора для обработки изображений в формате base64."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CustomUserCreateSerializer(UserCreateSerializer):
    """Пользовательский сериализатор для создания пользователя."""
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'password')

    def validate_username(self, username):
        """Проверка имени пользователя на допустимые символы."""
        check_symbols = re.sub(r'[\w.@+-]', '', username)
        if check_symbols:
            bad_symbols = ''.join(set(check_symbols))
            raise serializers.ValidationError(
                'В Имени пользователя использованы запрещённые символы: '
                f'{bad_symbols} '
                'Введите корректное имя пользователя. '
                'username может содержать только латинские буквы, '
                'символы @/./+/-/_ и цифры.'
            )
        return username


class AuthorSerializer(UserSerializer):
    """Сериализатор для пользователя."""
    class Meta(UserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки."""
    email = serializers.EmailField(source='subcripe.email', required=False)
    username = serializers.CharField(
        source='subcripe.username', required=False)
    first_name = serializers.CharField(
        source='subcripe.first_name', required=False)
    last_name = serializers.CharField(
        source='subcripe.last_name', required=False)
    is_subscribed = serializers.BooleanField(
        source='subcripe.is_subscribed', required=False)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = ('author', 'recipes', 'subcripe')

    def get_recipes_count(self, obj):
        """Получение количества рецептов в подписке."""
        return obj.recipes.count()

    def validate(self, attrs):
        """Проверка наличия подписки и возможности подписки."""
        request = self.context.get('request')
        if request.method == 'POST':
            subscribe_user = get_object_or_404(
                User,
                pk=self.context['view'].kwargs.get('id'))

            if request.user == subscribe_user:
                raise serializers.ValidationError(
                    'Подписатся на саму себя невозможно.')

            if Subscription.objects.filter(author=request.user,
                                           subcripe=subscribe_user).exists():
                raise serializers.ValidationError(
                    'Вы уже подписались на этого пользователя.')
        return attrs

    def to_representation(self, instance):
        """Преобразование данных перед выводом."""
        representation = super().to_representation(instance)
        request = self.context['request']
        recipes_list = instance.recipes.all()
        if request.method == 'GET':
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit and recipes_limit.isdigit():
                recipes_list = recipes_list[:int(recipes_limit)]
            representation['recipes_count'] = len(recipes_list)

        representation['recipes'] = RecipeShortSerializer(recipes_list,
                                                          many=True).data
        return representation


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента."""
    id = serializers.IntegerField(required=True)
    amount = serializers.IntegerField(required=True)
    name = serializers.CharField(required=False)
    measurement_unit = serializers.CharField(required=False)

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('name', 'measurement_unit')

    def validate_amount(self, amount):
        """Валидация количества ингредиента."""
        if amount < 1:
            raise serializers.ValidationError(
                'Количество ингредиента не должно быть меньше 1')
        return amount

    def validate_id(self, id):
        """Валидация идентификатора ингредиента."""
        if not Ingredient.objects.filter(pk=id).exists():
            raise serializers.ValidationError(
                f'Был указан несуществующий ингредиент {id}')
        return id

    def to_representation(self, instance):
        """Преобразование данных перед выводом."""
        representation = super().to_representation(instance)
        if ('request' in self.context and
                'amount' not in self.context['request'].GET):
            representation.pop('amount')
        return representation


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = ('name', 'color', 'slug')


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткий сериализатор рецепта."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания рецепта."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    ingredients = IngredientSerializer(many=True)
    author = AuthorSerializer(required=False)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(required=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time')
        read_only_fields = ('author',)

    def validate(self, attrs):
        """Проверка наличие обязательных полей и их заполненность рецепта."""
        if self.context['request'].method in ('POST', 'PATCH'):
            for field in ('tags', 'ingredients'):
                if field not in attrs.keys():
                    raise serializers.ValidationError(
                        f'Поля {field} не существует.')
            for field, value in attrs.items():
                if not value:
                    raise serializers.ValidationError(
                        f'Поле {field} не может быть пустой ')
        return attrs

    def validate_cooking_time(self, cooking_time):
        """Проверка времени приготовления."""
        if cooking_time < 1:
            raise serializers.ValidationError('Количество время приготовления '
                                              'не должно быть меньше 1')
        return cooking_time

    def validate_ingredients(self, ingredients):
        """Проверка списка ингредиентов."""
        ids = set()
        for ingredient_data in ingredients:
            if ingredient_data['id'] in ids:
                raise serializers.ValidationError(
                    "Был указан повторяющиеся ингредиенты")
            ids.add(ingredient_data['id'])

        return ingredients

    def validate_tags(self, tags):
        """Проверка списка тегов."""
        ids = set()
        for tag_id in tags:
            if tag_id in ids:
                raise serializers.ValidationError(
                    "Был указан повторяющиеся тег")
            ids.add(tag_id)
        return tags

    def create(self, validated_data):
        """Создание нового рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients', [])

        recipe = Recipe.objects.create(**validated_data)

        for tag in tags:
            tag = get_object_or_404(Tag, pk=tag.pk)
            recipe.tags.add(tag)

        for ingredient_data in ingredients:
            ingredient = get_object_or_404(Ingredient,
                                           pk=ingredient_data['id'])
            ingredient.amount = ingredient_data['amount']
            ingredient.save()
            recipe.ingredients.add(ingredient)

        return recipe

    def update(self, instance, validated_data):
        """Обновление существующего рецепта."""
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        tag_lst, ingredient_lst = [], []

        if tags_data is not None:
            for tag in tags_data:
                tag_lst.append(get_object_or_404(Tag, pk=tag.pk))

            instance.tags.set(tag_lst)

        if ingredients_data is not None:
            for ingredient_data in ingredients_data:
                ingredient = get_object_or_404(Ingredient,
                                               pk=ingredient_data['id'])
                ingredient.amount = ingredient_data['amount']
                ingredient.save()
                ingredient_lst.append(ingredient)

            instance.ingredients.set(ingredient_lst)

        instance.save()
        return instance

    def to_representation(self, instance):
        """Преобразование объекта в представление."""
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True).data
        representation['ingredients'] = IngredientSerializer(
            instance.ingredients.all(), many=True).data

        return representation


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного."""
    id = serializers.IntegerField(source='recipe.id', required=False)
    name = serializers.CharField(source='recipe.name', required=False)
    image = serializers.ImageField(source='recipe.image', required=False)
    cooking_time = serializers.IntegerField(source='recipe.cooking_time',
                                            required=False)

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'author', 'recipe')

    def validate(self, attrs):
        """Проверка данных перед сохранением."""
        request = self.context['request']
        self.post_validate_recipe_exists(request, Favorite)
        return attrs

    def post_validate_recipe_exists(self, request, model):
        """Проверка существования рецепта."""
        if request.method == 'POST':
            recipe = Recipe.objects.filter(
                pk=self.context['view'].kwargs.get('id'))
            model = model.objects.filter(author=request.user,
                                         recipe=recipe.first())
            if not recipe.exists():
                raise serializers.ValidationError(
                    "Нельзя добавить несуществующий рецепт "
                    f"в {MODEL_NAME[model.model.__name__]}.")
            if model.exists():
                raise serializers.ValidationError(
                    {"errors": "Рецепт уже есть "
                               f"в {MODEL_NAME[model.model.__name__]}."})


class ShoppingCartSerializer(FavoriteSerializer):
    """Сериализатор списка покупок."""
    class Meta(FavoriteSerializer.Meta):
        model = ShoppingCart

    def validate(self, attrs):
        """Проверка данных перед сохранением."""
        request = self.context['request']
        self.post_validate_recipe_exists(request, ShoppingCart)
        return attrs
