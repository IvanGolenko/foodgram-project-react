from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (
    Ingredient, Tag,
    IngredientInRecipe, Recipe, Favorite, ShoppingCart,
)
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    ReadOnlyField,
    PrimaryKeyRelatedField,
    ValidationError,
)
from users.models import User, Follower

FOLLOW_YOURSELF_VALIDATION_ERROR = 'Невозможно подписаться на себя'
ALREADY_FOLLOW_VALIDATION_ERROR = 'Вы подписаны на этого пользователя'
NOT_FOLLOW_VALIDATION_ERROR = 'Вы не подписаны на этого пользователя'
NOT_INFORMATION_VALIDATION_ERROR = 'Данные не предоставлены'
ALREDY_RECIPE_VALIDATION_ERROR = 'Рецепт уже есть в списке покупок'
NOT_RECIPE_VALIDATION_ERROR = 'Рецепта нет в списке покупок'
AMOUNT_VALIDATION_ERROR = 'Ингредиента должно быть больше 0'
UNIQUE_INGREDIENT_VALIDATION_ERROR = 'Ингредиент уже есть в рецепте'


class UserSerializer(ModelSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, item):
        user = self.context['request'].user
        return (user.subscribed.filter(subscribing__id=item.id)
                .exists()) if not user.is_anonymous else False


class UserDetailSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'password')


class IngredientsSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientInRecipeSerializer(ModelSerializer):
    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only = ['id', 'name', 'measurement_unit']


class AuthorRecipeSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(ModelSerializer):
    user = PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True)
    author = PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True)
    id = ReadOnlyField(source='author.id')
    email = ReadOnlyField(source='author.email')
    username = ReadOnlyField(source='author.username')
    first_name = ReadOnlyField(source='author.first_name')
    last_name = ReadOnlyField(source='author.last_name')
    is_subscribed = SerializerMethodField()
    recipes_count = SerializerMethodField()
    recipes = AuthorRecipeSerializer(
        source='author.recipe',
        many=True, read_only=True)

    class Meta:
        model = Follower
        fields = (
            'id', 'email',
            'username', 'first_name',
            'last_name', 'is_subscribed',
            'recipes', 'recipes_count',
            'user', 'author'
        )

    def validate(self, data):
        request = self.context.get('request')
        author_id = data['author'].id
        follow = Follower.objects.filter(user=request.user,
                                         author__id=author_id).exists()
        if request.method == 'GET':
            if request.user.id == author_id:
                raise ValidationError(
                    FOLLOW_YOURSELF_VALIDATION_ERROR
                )
            if follow:
                raise ValidationError(
                    ALREADY_FOLLOW_VALIDATION_ERROR
                )
        if request.method == 'DELETE':
            if not follow:
                raise ValidationError(
                    NOT_FOLLOW_VALIDATION_ERROR
                )
        return data

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Follower.objects.filter(user=obj.user,
                                       author=obj.author).exists()

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()


class RecipeSerializer(ModelSerializer):
    image = Base64ImageField()
    author = UserDetailSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredient',
        many=True, read_only=True,)
    is_favorited = SerializerMethodField(default=False)
    is_in_shopping_cart = SerializerMethodField(default=False)

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user,
            recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user,
            recipe=obj).exists()

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        ingredients_set = set()
        for ingredient in ingredients:
            if int(ingredient.get('amount')) <= 0:
                raise ValidationError(
                    AMOUNT_VALIDATION_ERROR
                )
            id = ingredient.get('id')
            if id in ingredients_set:
                raise ValidationError(
                    UNIQUE_INGREDIENT_VALIDATION_ERROR
                )
            ingredients_set.add(id)
        data['ingredients'] = ingredients
        return data

    def create(self, validated_data):
        image = validated_data.pop('image')
        ingredients = validated_data.pop('ingredients')
        tags = self.initial_data.get('tags')
        recipe = Recipe.objects.create(image=image, **validated_data)
        for tag_id in tags:
            recipe.tags.add(get_object_or_404(Tag, pk=tag_id))
        for ingredient in ingredients:
            IngredientInRecipeSerializer.objects.create(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'))
        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        tags = self.initial_data.get('tags')
        for tag_id in tags:
            instance.tags.add(get_object_or_404(Tag, pk=tag_id))
        IngredientInRecipeSerializer.objects.filter(recipe=instance).delete()
        for ingredient in validated_data.get('ingredients'):
            ingredients_amounts = IngredientInRecipeSerializer.objects.create(
                recipe=instance,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'))
            ingredients_amounts.save()
        if validated_data.get('image') is not None:
            instance.image = validated_data.get('image')
        instance.name = validated_data.get('name')
        instance.text = validated_data.get('text')
        instance.cooking_time = validated_data.get('cooking_time')
        instance.save()
        return instance


class FavoriteRecipeSerializer(ModelSerializer):
    user = PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )
    recipe = PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
    )

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class ShoppingCartSerializer(ModelSerializer):
    user = PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True)
    recipe = PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        write_only=True)
    id = ReadOnlyField(source='recipe.id')
    name = ReadOnlyField(source='recipe.name')
    image = SerializerMethodField()
    cooking_time = ReadOnlyField(
        source='recipe.cooking_time')

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time', 'user', 'recipe')

    def get_image(self, obj):
        request = self.context.get('request')
        photo_url = obj.recipe.image.url
        return request.build_absolute_uri(photo_url)

    def validate(self, data):
        request = self.context.get('request')
        recipe_id = data['recipe'].id
        shopping_cart = ShoppingCart.objects.filter(
            user=request.user,
            recipe__id=recipe_id).exists()
        if request.method == 'GET':
            if request.user.is_anonymous:
                raise ValidationError(
                    NOT_INFORMATION_VALIDATION_ERROR
                )
            if shopping_cart:
                raise ValidationError(
                    ALREDY_RECIPE_VALIDATION_ERROR
                )
        if request.method == 'DELETE':
            if not shopping_cart:
                raise ValidationError(
                    NOT_RECIPE_VALIDATION_ERROR
                )
        return data
