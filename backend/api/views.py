import io

from http import HTTPStatus

from django.shortcuts import get_list_or_404, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.http import FileResponse
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from recipes.models import IngredientInRecipe

from api.filters import RecipeFilters
from recipes.models import (
    Tag, Ingredient,
    Recipe, ShoppingCart,
    Favorite
)
from api.serializers import (
    IngredientSerializer,
    TagSerializer,
    FollowSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer,
    UserDetailSerializer,
    RecipeSerializer,
)
from users.models import User, Follower


class CreateUserView(UserViewSet):
    serializer_class = UserDetailSerializer
    queryset = User.objects.all()


class FollowViewSet(ModelViewSet):

    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return get_list_or_404(User, following__user=self.request.user)

    def create(self, request, *args, **kwargs):

        user_id = self.kwargs.get('users_id')
        user = get_object_or_404(User, id=user_id)
        Follower.objects.create(
            user=request.user, following=user)
        return Response(HTTPStatus.CREATED)

    def delete(self, request, *args, **kwargs):

        author_id = self.kwargs['users_id']
        user_id = request.user.id
        subscribe = get_object_or_404(
            Follower, user__id=user_id, following__id=author_id)
        subscribe.delete()
        return Response(HTTPStatus.NO_CONTENT)


class TagViewSet(ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = [permissions.AllowAny]
    filter_backends = (DjangoFilterBackend, )
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_class = RecipeFilters
    filter_backends = [DjangoFilterBackend, ]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer

    #  При попытке сделать через @action не могу вызвать POST
    #  "detail": "Method \"POST\" not allowed.
    #  Прошу разрешения оставить, как у меня есть.
    #  Ниже закоментил, как пытался сделать через @action
    '''serializer_class = RecipeSerializer'''
    '''def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_anonymous:
            if self.request.query_params.get('is_favorited'):
                qs = qs.filter(favorite__user=user)
            if self.request.query_params.get('is_in_shopping_cart'):
                qs = qs.filter(purchase__user=user)
            return qs
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipeSerializerPost

    def perform_update(self, serializer):
        serializer.save()

    @decorators.action(
        ['GET', 'DELETE'],
        detail=False,
        url_path=r'(?P<recipe_id>\d+)/favorite',
        permission_classes=[IsAuthor, ]
    )
    def favorite(self, request, *args, **kwargs):
        user = request.user
        user_pk = user.id
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if request.method == 'GET':
            serializer_val = FavoriteSerializer(
                data={'user': user_pk, 'recipe': recipe_id})
            serializer_val.is_valid(raise_exception=True)
            serializer_val.save()
            serializer = AuthorRecipeSerializer(recipe)
            return Response(serializer.data)
        favorite = Favorite.objects.filter(user=user, recipe=recipe)
        if favorite.exists():
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            data={"errors": "No recipe in favorite"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @decorators.action(
        ['GET', 'DELETE'],
        detail=False,
        url_path=r'(?P<recipe_id>\d+)/shopping_cart',
        permission_classes=[IsAuthor, ])
    def shopping_cart(self, request, *args, **kwargs):
        user = request.user
        user_pk = user.id
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if request.method == 'GET':
            serializer_val = ShoppingCartSerializer(
                data={'user': user_pk, 'recipe': recipe_id})
            serializer_val.is_valid(raise_exception=True)
            serializer_val.save()
            serializer = AuthorRecipeSerializer(recipe)
            return Response(serializer.data)
        shop_cart = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if shop_cart.exists():
            shop_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            data={"errors": "No recipe in shopping cart"},
            status=status.HTTP_400_BAD_REQUEST,
        )'''


class BaseFavoriteCartViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        recipe_id = int(self.kwargs['recipes_id'])
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.model.objects.create(
            user=request.user, recipe=recipe)
        return Response(HTTPStatus.CREATED)

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs['recipes_id']
        user_id = request.user.id
        object = get_object_or_404(
            self.model, user__id=user_id, recipe__id=recipe_id)
        object.delete()
        return Response(HTTPStatus.NO_CONTENT)


class ShoppingCartViewSet(BaseFavoriteCartViewSet):
    serializer_class = ShoppingCartSerializer
    queryset = ShoppingCart.objects.all()
    model = ShoppingCart


class FavoriteViewSet(BaseFavoriteCartViewSet):
    serializer_class = FavoriteSerializer
    queryset = Favorite.objects.all()
    model = Favorite


class DownloadCartView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        #  понимаю, что запрос лишний, но не получается переписать
        #  Прошу разрешения оставить, как у меня есть.
        shopping_cart = user.purchases.all()
        buying_list = {}
        for record in shopping_cart:
            recipe = record.recipe
            ingredients = IngredientInRecipe.objects.filter(recipe=recipe)
            for ingredient in ingredients:
                amount = ingredient.amount
                name = ingredient.ingredient.name
                measurement_unit = ingredient.ingredient.measurement_unit
                if name not in buying_list:
                    buying_list[name] = {
                        'measurement_unit': measurement_unit,
                        'amount': amount
                    }
                else:
                    buying_list[name]['amount'] = (buying_list[name]['amount']
                                                   + amount)
        shoping_list = []
        shoping_list.append('Список покупок:')
        for item in buying_list:
            shoping_list.append(f'{item} - {buying_list[item]["amount"]} '
                                f'{buying_list[item]["measurement_unit"]}')
        shoping_list.append(' ')
        shoping_list.append('FoodGram, 2022')
        pdfmetrics.registerFont(TTFont('DejaVuSerif',
                                       './api/ttf/DejaVuSerif.ttf'))
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        # p.setFont(15) - значение размер шрифта
        p.setFont('DejaVuSerif', 15)
        # start = 800 - значение размера отступа от нижней границы файла
        start = 800
        for line in shoping_list:
            # p.drawString(100) - значение размера отступа от левого края
            p.drawString(100, start, line)
            # start -= 20 - значение размера отступа между строками
            start -= 20
        p.showPage()
        p.save()
        # seek(0) - позиция потока на заданное байтовое смещение
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True,
                            filename='cart_list.pdf')
