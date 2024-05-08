from django.shortcuts import get_object_or_404
from rest_framework import viewsets, validators, permissions, mixins

from recipes.models import Recipe
from .permissions import IsAuthorOrReadOnly

MODEL_NAME = {"Favorite": "избранное", "ShoppingCart": "список покупок"}


class CreateDestroyViewSets(mixins.CreateModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet):
    """Представления для создания и удаления объектов."""
    permission_classes = (IsAuthorOrReadOnly,)
    lookup_url_kwarg = 'id'

    def get_object(self):
        """Получает объект для просмотра или удаления."""
        queryset = self.filter_queryset(self.get_queryset())
        if self.request.method == 'DELETE':
            if self.get_recipe() and not queryset.filter(
                    author=self.request.user,
                    recipe_id=self.kwargs.get('id')).exists():
                raise validators.ValidationError(
                    {'errors': f'Этот рецепт не добавлен в '
                     f'{MODEL_NAME[queryset.model.__name__]}.'})
        obj = get_object_or_404(queryset, author=self.request.user,
                                recipe=self.get_recipe())
        self.check_object_permissions(self.request, obj)
        return obj

    @staticmethod
    def update_attribute(instance, attribute, value=False):
        """Обновляет атрибут экземпляра модели."""
        setattr(instance, attribute, value)
        instance.save()

    def get_recipe(self):
        """Получает объект рецепта."""
        return get_object_or_404(Recipe, pk=self.kwargs.get('id'))


class IngredientTagViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для чтения списка ингредиентов и тегов."""
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
