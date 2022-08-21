from colorfield.fields import ColorField

from django.core.validators import MinValueValidator
from django.db import models

from users.models import User

COOKING_TIME_ERROR = 'Время приготовление должно быть больше 0'
AMOUNT_INGREDIENT_ERROR = 'Количество ингредиента должно быть больше 0'


class Tag(models.Model):
    """Модель для тегов."""
    name = models.CharField(
        verbose_name='Наименование Тэга',
        max_length=200,
        unique=True,
    )
    color = ColorField(
        verbose_name='Цветовой HEX-код',
        unique=True,
        default='#FF0000',
    )
    slug = models.SlugField(
        verbose_name='Уникальный идентификатор тэга',
        max_length=200,
        unique=True,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель для ингредиента."""
    name = models.CharField(
        verbose_name='Ингридиент',
        max_length=200,
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=30,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингридиент',
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель для рецептов."""
    name = models.CharField(
        verbose_name='Название блюда',
        max_length=200,
        unique=True
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        related_name='recipes',
        on_delete=models.CASCADE,
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        through='TagInRecipe',
    )
    image = models.CharField(
        verbose_name='Изображение блюда',
        max_length=10000,
    )
    text = models.TextField(
        verbose_name='Описание блюда',
        help_text='Заполните описание рецепта',
        max_length=300,
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        help_text='Введите время приготовления в минутах',
        default=0,
        validators=(MinValueValidator(1, COOKING_TIME_ERROR),),
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты блюда',
        through='IngredientInRecipe',
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class TagInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )
    tag = models.ForeignKey(
        Tag,
        verbose_name='Тег',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Тег в рецепте'
        verbose_name_plural = 'Теги в рецептах'

    def __str__(self):
        return f'{self.recipe} {self.tag}'


class IngredientInRecipe(models.Model):
    """Модель для хранения количества ингредиентов."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='В каких рецептах',
        related_name='recipe_ingredients',
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        verbose_name='Связанные ингредиенты',
        related_name='ingredients_recipe',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингридиента',
        default=1,
        validators=(MinValueValidator(1, AMOUNT_INGREDIENT_ERROR),)
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Количество ингридиентов'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredients'), name='unique_ingredient'
            ),
        )

    def __str__(self):
        return self.ingredients.name


class ShoppingCart(models.Model):
    """Модель для корзины рецептов."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='ingredient_list',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='ingredient_list_user',
    )
    date_added = models.DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Список ингридиентов'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='unique_list'
            ),
        )


class Favorite(models.Model):
    """Модель для избранных рецептов пользователя."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
        blank=False,
        null=True,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites',
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['user']
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='favorite_unique'
        ), ]

    def __str__(self):
        return f'Рецепт {self.recipe} добавлен в избранное {self.user}'
