from colorfield.fields import ColorField
from django.core.validators import MinValueValidator
from django.db import models
from users.models import User

COOKING_TIME_ERROR = 'Время приготовление должно быть больше 0'
AMOUNT_INGREDIENT_ERROR = 'Количество ингредиента должно быть больше 0'


class Ingredient(models.Model):
    """Модель для ингредиента."""
    name = models.CharField(
        verbose_name='Ингредиент',
        max_length=50,
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=50,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент',
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель для тегов."""
    name = models.CharField(
        verbose_name='Наименование тэга',
        max_length=30,
        unique=True,
    )
    color = ColorField(
        format='hex',
        verbose_name='Цветовой HEX-код',
        unique=True,
        default='#FF0000',
    )
    slug = models.SlugField(
        verbose_name='Текстовый идентификатор тэга',
        max_length=30,
        unique=True,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель для рецептов."""
    name = models.CharField(
        verbose_name='Название блюда',
        max_length=50,
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
    image = models.ImageField(
        verbose_name='Изображение блюда',
        upload_to='recipes/image/'
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
        validators=(MinValueValidator(0.5, COOKING_TIME_ERROR),),
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
        related_name='recipes'
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class ShoppingCart(models.Model):
    """Модель для корзины рецептов."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='purchases',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='carts',
    )
    date_added = models.DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='unique_cart'
            ),
        )

    def __str__(self):
        return f'{self.user} {self.recipe}'


class IngredientInRecipe(models.Model):
    """Модель для хранения количества ингредиентов."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Выберите рецепт',
        related_name='ingredient_recipes',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Продукты в рецепте',
        related_name='ingredient_recipes',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента',
        default=0.1,
        validators=(MinValueValidator(0.1, AMOUNT_INGREDIENT_ERROR),)
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique_ingredientrecipe'
            ),
        ]

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


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
        constraints = [
            models.UniqueConstraint(fields=['tag', 'recipe'],
                                    name='unique_tagrecipe')
        ]

    def __str__(self):
        return f'{self.tag} {self.recipe}'


class Favorite(models.Model):
    """Модель для избранных рецептов пользователя."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
        blank=False,
        null=False,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites',
        null=False,
        blank=False,
    )

    class Meta:
        ordering = ['user']
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_favorite'
        ), ]

    def __str__(self):
        return f'Рецепт {self.recipe} добавлен в избранное {self.user}'
