from http import HTTPStatus

from django.shortcuts import get_object_or_404
from recipes.models import Recipe
from api.serializers import AuthorRecipeSerializer
from rest_framework.response import Response


def post_delete_favorite_shopping_cart(user, method, model, id):
    recipe = get_object_or_404(Recipe, id=id)
    if method == 'POST':
        model.objects.create(user=user, recipe=recipe)
        serializer = AuthorRecipeSerializer(recipe)
        return Response(serializer.data, status=HTTPStatus.CREATED)
    obj = get_object_or_404(model, user=user, recipe=recipe)
    obj.delete()
    return Response(status=HTTPStatus.NO_CONTENT)


def recipe_formation(ingredients):
    return '\n'.join([
        f'{ingredient["ingredient__name"]} - {ingredient["sum_amount"]}'
        f'{ingredient["ingredient__measurement_unit"]}'
        for ingredient in ingredients
    ])
