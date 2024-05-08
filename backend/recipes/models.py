from django.contrib.auth.models import AbstractUser
from django.db import models

MAX_LENGTH = 150
RECIPE_MIN_VALUE = 1


class FoodGramUser(AbstractUser):
    """Пользователь FoodGram."""
    email = models.EmailField('Адрес электронной почты', unique=True,
                              max_length=254)
    username = models.CharField('Имя пользователя', unique=True,
                                max_length=MAX_LENGTH)
    first_name = models.CharField('Имя', max_length=MAX_LENGTH)
    last_name = models.CharField('Фамилия', max_length=MAX_LENGTH)
    is_subscribed = models.BooleanField('Подписка', default=False)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username[:30]


class Tag(models.Model):
    """Тег для рецептов."""
    name = models.CharField('Имя', max_length=16)
    color = models.CharField('Цвет', max_length=16)
    slug = models.SlugField('Идентификатор', unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """Ингредиент для рецептов."""
    name = models.CharField('Имя', max_length=MAX_LENGTH)
    measurement_unit = models.CharField('Единица', max_length=MAX_LENGTH)
    amount = models.IntegerField('Количество', default=0)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    """Рецепт блюда."""
    name = models.CharField('Название', max_length=200)
    text = models.TextField('Описание')
    image = models.ImageField('Картинка', upload_to='recipes/images/')
    cooking_time = models.PositiveIntegerField('Время приготовления',
                                               default=0)
    tags = models.ManyToManyField(Tag, verbose_name='Тег')
    ingredients = models.ManyToManyField(
        Ingredient, verbose_name='Ингредиент',)
    author = models.ForeignKey(
        FoodGramUser, on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    is_favorited = models.BooleanField('Избранное', default=False, blank=True)
    is_in_shopping_cart = models.BooleanField('Приобретение', default=False,
                                              blank=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name


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
    recipes = models.ManyToManyField("Recipe", verbose_name='Рецепты')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self) -> str:
        return self.author.username
