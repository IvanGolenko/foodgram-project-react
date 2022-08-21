from django.http import HttpResponse
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser import views
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated


from api.filters import RecipeFilters
from api.paginators import RecipePaginator
from recipes.models import (
    Tag, Ingredient,
    Recipe, IngredientInRecipe,
    ShoppingCart, Favorite
)
from api.serializers import (
    UserSerializer,
    IngredientsSerializer,
    TagSerializer,
    FollowSerializer,
    RecipeSerializer,
    FavoriteRecipeSerializer,
    ShoppingCartSerializer
)
from users.models import User, Follower

SHOPPING_CART_ADD_MESSAGE = 'Рецепт успешно добавлен в корзину'
SHOPPING_CART_DELETE_MESSAGE = 'Рецепт успешно удален из списка покупок'


class CustomUserViewSet(views.UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = RecipePaginator

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = Follower.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=['GET', 'DELETE'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        user = get_object_or_404(User, username=request.user.username)
        author = get_object_or_404(User, id=id)
        data = {
            'user': user.id,
            'author': author.id,
        }
        serializer = FollowSerializer(
            data=data, context={'request': request})
        if request.method == 'GET' and serializer.is_valid(
                raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        serializer.is_valid(raise_exception=True)
        follow = get_object_or_404(Follower, user=user, author=author)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    serializer_class = IngredientsSerializer
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny, )
    filter_backends = (DjangoFilterBackend, )
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = RecipePaginator
    filter_backends = [DjangoFilterBackend]
    filter_class = RecipeFilters
    ordering_fields = ('date_pub')

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Recipe.objects.all()
        queryset = Recipe.objects.annotate(
            is_favorited=Exists(Favorite.objects.filter(
                user=user, recipe_id=OuterRef('pk'))),
            is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                user=user, recipe_id=OuterRef('pk'))))
        if self.request.GET.get('is_favorited'):
            return queryset.filter(is_favorited=True)
        elif self.request.GET.get('is_in_shopping_cart'):
            return queryset.filter(is_in_shopping_cart=True)

        return queryset

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    @action(detail=True,
            methods=['GET', 'DELETE'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        user = get_object_or_404(User, username=request.user.username)
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {
            'user': user.id,
            'recipe': recipe.id}
        serializer = FavoriteRecipeSerializer(
            data=data, context={'request': request})
        if request.method == 'GET' and serializer.is_valid(
                raise_exception=True):
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED)
        serializer.is_valid(raise_exception=True)
        favorite = get_object_or_404(Favorite,
                                     user=user,
                                     recipe=recipe)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['GET', 'DELETE'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = get_object_or_404(User, username=request.user.username)
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {
            'user': user.id,
            'recipe': recipe.id}
        serializer = ShoppingCartSerializer(
            data=data, context={'request': request})
        if request.method == 'GET' and serializer.is_valid(
                raise_exception=True):
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED)
        serializer.is_valid(raise_exception=True)
        favorite = get_object_or_404(ShoppingCart,
                                     user=user,
                                     recipe=recipe)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        buying_list = {}
        shopping_cart = IngredientInRecipe.objects.filter(
            recipe__ingredient_list__user=request.user
        ).values_list(
            'amount',
            'ingredients__name',
            'ingredients__measurement_unit',
            named=True
        ).order_by('id')
        for ingredient in shopping_cart:
            measurement_unit = ingredient.ingredients__measurement_unit
            name = ingredient.ingredients__name
            amount = ingredient.amount

            if name not in buying_list:
                buying_list[name] = {
                    'amount': amount,
                    'measurement_unit': measurement_unit,
                }
            else:
                buying_list[name]['amount'] = (buying_list[name]['amount']
                                               + amount)
        wishlist = []
        for item in buying_list:
            wishlist.append(f'{item} - {buying_list[item]["amount"]}'
                            f' {buying_list[item]["measurement_unit"]} \n')

        response = HttpResponse(wishlist, 'Content-Type: text/plain')
        response['Content-Disposition'] = 'attachment; filename="wishlist.txt"'
        return response
