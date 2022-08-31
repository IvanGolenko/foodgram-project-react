from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (
    Serializer,
    ModelSerializer,
    SerializerMethodField,
    ReadOnlyField,
    PrimaryKeyRelatedField,
    ValidationError,
    IntegerField,
    ImageField,
    SerializerMetaclass,
    CharField
)

from recipes.models import (
    Ingredient, Tag, TagInRecipe,
    IngredientInRecipe, Recipe, Favorite, ShoppingCart,
)
from users.models import User, Follower

UNIQUE_INGREDIENT_VALIDATION_ERROR = 'Ингредиент уже есть в рецепте'
NOT_INGREDIENT_VALIDATION_ERROR = 'Ингредиента нет в базе'


class UserSerializer(metaclass=SerializerMetaclass):
    is_subscribed = SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        if Follower.objects.filter(
                user=request.user, following__id=obj.id).exists():
            return True
        return False


class UserDetailSerializer(UserCreateSerializer, UserSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'is_subscribed', 'password')
        write_only_fields = ('password',)
        read_only_fields = ('id',)
        extra_kwargs = {'is_subscribed': {'required': False}}

    def to_representation(self, obj):
        result = super(UserDetailSerializer, self).to_representation(obj)
        result.pop('password', None)
        return result


class CommonRecipe(metaclass=SerializerMetaclass):
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        if Favorite.objects.filter(user=request.user,
                                   recipe__id=obj.id).exists():
            return True

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        if ShoppingCart.objects.filter(user=request.user,
                                       recipe__id=obj.id).exists():
            return True


class CommonCount(metaclass=SerializerMetaclass):
    recipes_count = SerializerMethodField()

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author__id=obj.id).count()


class IngredientSerializer(ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        extra_kwargs = {'name': {'required': False},
                        'measurement_unit': {'required': False}}


class IngredientInRecipeSerializer(ModelSerializer):
    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientEditSerializer(ModelSerializer):
    id = IntegerField(source='ingredient.id')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class FavoriteSerializer(Serializer):
    id = IntegerField()
    name = CharField()
    cooking_time = IntegerField()
    image = Base64ImageField(max_length=None, use_url=False,)


class ShoppingCartSerializer(Serializer):
    id = IntegerField()
    name = CharField()
    cooking_time = IntegerField()
    image = Base64ImageField(max_length=None, use_url=False,)


class RecipeSerializer(ModelSerializer,
                       CommonRecipe):
    image = ImageField(
        max_length=None,
        required=True,
        allow_empty_file=False,
        use_url=True,
    )
    author = UserDetailSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = IngredientInRecipeSerializer(
        source='ingredientrecipes',
        many=True)
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name', 'image', 'text',
                  'ingredients', 'tags', 'cooking_time',
                  'is_in_shopping_cart', 'is_favorited')


class RecipeSerializerPost(ModelSerializer,
                           CommonRecipe):
    author = UserDetailSerializer(read_only=True)
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True)
    ingredients = IngredientEditSerializer(
        source='ingredientrecipes', many=True)
    image = Base64ImageField(max_length=None, use_url=False,)

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name', 'image', 'text',
                  'ingredients', 'tags', 'cooking_time',
                  'is_in_shopping_cart', 'is_favorited')

    def validate_ingredients(self, value):
        ingredients_list = []
        ingredients = value
        for ingredient in ingredients:
            id_to_check = ingredient['ingredient']['id']
            ingredient_to_check = Ingredient.objects.filter(id=id_to_check)
            if not ingredient_to_check.exists():
                raise ValidationError(
                    NOT_INGREDIENT_VALIDATION_ERROR)
            if ingredient_to_check in ingredients_list:
                raise ValidationError(
                    UNIQUE_INGREDIENT_VALIDATION_ERROR)
            ingredients_list.append(ingredient_to_check)
        return value

    #  считаю, что вынесение фильтра в переменную невозможно,
    #  т.к. фильтрация происходит по разным параметрам
    def add_tags_and_ingredients(self, tags_data, ingredients, recipe):
        for tag_data in tags_data:
            recipe.tags.add(tag_data)
            recipe.save()
        for ingredient in ingredients:
            if not IngredientInRecipe.objects.filter(
                    ingredient_id=ingredient['ingredient']['id'],
                    recipe=recipe).exists():
                ingredientrecipe = IngredientInRecipe.objects.create(
                    ingredient_id=ingredient['ingredient']['id'],
                    recipe=recipe)
                ingredientrecipe.amount = ingredient['amount']
                ingredientrecipe.save()
            else:
                IngredientInRecipe.objects.filter(
                    recipe=recipe).delete()
                recipe.delete()
                raise ValidationError(
                    UNIQUE_INGREDIENT_VALIDATION_ERROR)
        return recipe

    def create(self, validated_data):
        author = validated_data.get('author')
        tags_data = validated_data.pop('tags')
        name = validated_data.get('name')
        image = validated_data.get('image')
        text = validated_data.get('text')
        cooking_time = validated_data.get('cooking_time')
        ingredients = validated_data.pop('ingredientrecipes')
        recipe = Recipe.objects.create(
            author=author,
            name=name,
            image=image,
            text=text,
            cooking_time=cooking_time,
        )
        recipe = self.add_tags_and_ingredients(tags_data, ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredientrecipes')
        TagInRecipe.objects.filter(recipe=instance).delete()
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        instance = self.add_tags_and_ingredients(
            tags_data, ingredients, instance)
        super().update(instance, validated_data)
        instance.save()
        return instance

    #  при попытке сделать через метод bulk_create() получаю ошибку.
    #  gрошу разрешения оставить, как у меня есть.
    #  Ниже закоментил, как пытался сделать через bulk_create().
    ''' def add_tags_and_ingredients(self, tags_data, ingredients, recipe):
        for tag_data in tags_data:
            recipe.tags.add(tag_data)
            recipe.save()
        bulk = []
        for ingredient in ingredients:
            if not Ingredient_filter(
                    ingredient_id=ingredient['ingredient']['id'],
                    recipe=recipe).exists():
                bulk.append(IngredientInRecipe(ingredient_id=ingredient['ingredient']['id'],
                                               recipe=recipe,
                                               amount=ingredient['amount']))
            else:
                Ingredient_filter(
                    recipe=recipe).delete()
                recipe.delete()
                raise ValidationError(
                    UNIQUE_INGREDIENT_VALIDATION_ERROR)
        IngredientInRecipe.objects.bulk_create(bulk)
        return recipe '''


class AuthorRecipeSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(ModelSerializer,
                       UserSerializer, CommonCount):
    recipes = SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        queryset = Recipe.objects.filter(author__id=obj.id)
        if request.GET.get('recipes_limit'):
            recipes_limit = int(request.GET.get('recipes_limit'))
            queryset = queryset[:recipes_limit]
        return AuthorRecipeSerializer(queryset, many=True).data
