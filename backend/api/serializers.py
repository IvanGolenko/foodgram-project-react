from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (
    Ingredient, Tag, IngredientInRecipe,
    Recipe, Favorite, ShoppingCart)
from rest_framework.serializers import (
    CharField,
    ImageField,
    IntegerField,
    ModelSerializer,
    PrimaryKeyRelatedField,
    ReadOnlyField,
    Serializer,
    SerializerMethodField,
    SerializerMetaclass,
    ValidationError
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
        source='ingredient_recipes',
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
        source='ingredient_recipes', many=True)
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

    def create_ingredients(ingredients, recipe):
        IngredientInRecipe.objects.bulk_create(
            [
                IngredientInRecipe(
                    ingredient_id=ingredient['ingredient']['id'],
                    recipe=recipe,
                    amount=ingredient['amount']
                )
                for ingredient in ingredients
            ]
        )

    def create_tags(tags, recipe):
        recipe.tags.set(tags)

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredient_recipes')
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.create_tags(tags, recipe)
        self.create_ingredients(ingredients, recipe)
        recipe.save()
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.pop('name', instance.name)
        instance.image = validated_data.pop('image', instance.image)
        instance.text = validated_data.pop('text', instance.text)
        instance.cooking_time = validated_data.pop(
            'cooking_time',
            instance.cooking_time
        )
        instance.ingredients.clear()
        ingredients = validated_data.pop('ingredient_recipes')
        self.create_ingredients(ingredients, instance)
        instance.tags.clear()
        tags = validated_data.pop('tags')
        self.create_tags(tags, instance)
        return super().update(instance, validated_data)


class AuthorRecipeSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(Serializer):
    id = IntegerField()
    name = CharField()
    cooking_time = IntegerField()
    image = Base64ImageField(max_length=None, use_url=False,)


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
