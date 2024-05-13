from colorfield.fields import ColorField
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from module.constants import (
    ING_MAX_LENG, ING_MAX_AMOUNT_VALUE, ING_MIN_AMOUNT_VALUE,
    RECIPE_MAX_COOK_VALUE, RECIPE_MAX_LENG, RECIPE_MIN_COOK_VALUE,
    TAG_MAX_LENG, USER_MAX_LENG, USERNAME_LENG
)


class FoodGramUser(AbstractUser):
    """Пользователь FoodGram."""
    email = models.EmailField('Адрес электронной почты', unique=True)
    first_name = models.CharField('Имя', max_length=USER_MAX_LENG)
    last_name = models.CharField('Фамилия', max_length=USER_MAX_LENG)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username[:USERNAME_LENG]


class Tag(models.Model):
    """Тег для рецептов."""
    name = models.CharField('Имя', max_length=TAG_MAX_LENG)
    color = ColorField(verbose_name='Цвет')
    slug = models.SlugField(
        'Идентификатор',
        max_length=TAG_MAX_LENG,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """Ингредиент для рецептов."""
    name = models.CharField('Имя', max_length=ING_MAX_LENG)
    measurement_unit = models.CharField('Единица', max_length=ING_MAX_LENG)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    """Рецепт блюда."""
    name = models.CharField('Название', max_length=RECIPE_MAX_LENG)
    text = models.TextField('Описание')
    image = models.ImageField('Картинка', upload_to='recipes/images/')
    cooking_time = models.IntegerField(
        'Время приготовления',
        validators=[
            MinValueValidator(
                RECIPE_MIN_COOK_VALUE,
                message='Значение должно быть больше или равно %(value)s.'
            ),
            MaxValueValidator(
                RECIPE_MAX_COOK_VALUE,
                message='Значение должно быть меньше или равно %(value)s.'
            )
        ]
    )
    tags = models.ManyToManyField(Tag, verbose_name='Тег')
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиент',
        through='RecipeIngredient'
    )
    author = models.ForeignKey(
        FoodGramUser,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name


class RecipeIngredient(models.Model):
    """Промежуточная модель для хранения ингредиентов рецепта."""
    recipe = models.ForeignKey(
        'Recipe',
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        'Ingredient',
        verbose_name='Ингредиент',
        on_delete=models.CASCADE
    )
    amount = models.IntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                ING_MIN_AMOUNT_VALUE,
                message='Значение должно быть больше или равно %(value)s.'
            ),
            MaxValueValidator(
                ING_MAX_AMOUNT_VALUE,
                message='Значение должно быть меньше или равно %(value)s.'
            )
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'


class AuthorRecipeFieldsBase(models.Model):
    """Базовая модель для связи Избранные и Список покупоки."""
    author = models.ForeignKey(
        FoodGramUser,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепты'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'recipe'],
                name='unique_author_recipe'
            )
        ]


class Favorite(AuthorRecipeFieldsBase):
    """Избранный рецепт."""
    class Meta:
        verbose_name = 'Избранный'
        verbose_name_plural = 'Избранные'
        default_related_name = 'favorites'

    def __str__(self) -> str:
        return self.author.username


class ShoppingCart(AuthorRecipeFieldsBase):
    """Список покупок."""
    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупоки'
        default_related_name = 'shopcarts'

    def __str__(self) -> str:
        return self.author.username


class Subscription(models.Model):
    """Подписка на пользователя."""
    author = models.ForeignKey(
        FoodGramUser,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Автор'
    )
    subcripe = models.ForeignKey(
        FoodGramUser,
        on_delete=models.CASCADE,
        verbose_name='Подписка'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'subcripe'],
                name='unique_author_subcripe'
            )
        ]

    def __str__(self) -> str:
        return self.author.username
