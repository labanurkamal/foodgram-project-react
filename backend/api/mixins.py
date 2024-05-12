from rest_framework import viewsets, permissions


class IngredientTagViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для чтения списка ингредиентов и тегов."""
    pagination_class = None
    permission_classes = (permissions.AllowAny,)
