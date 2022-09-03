from django.contrib import admin

from recipes.models import (
    Favorite, Ingredient, IngredientInRecipe, Recipe,
    ShoppingCart, Tag, TagInRecipe
)


class IngredientRecipeInline(admin.TabularInline):

    model = IngredientInRecipe
    extra = 0


class TagRecipeInline(admin.TabularInline):

    model = TagInRecipe
    extra = 0


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):

    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name', )
    empty_value_display = '-пусто-'
    list_filter = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):

    list_display = ('name', 'color', 'slug')
    search_fields = ('name', )
    empty_value_display = '-пусто-'
    list_filter = ('name',)


@admin.register(ShoppingCart)
class CartAdmin(admin.ModelAdmin):

    list_display = ('user', 'recipe', 'id')
    search_fields = ('user', )
    empty_value_display = '-пусто-'
    list_filter = ('user',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):

    list_display = ('user', 'recipe')
    search_fields = ('user', )
    empty_value_display = '-пусто-'
    list_filter = ('user',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):

    inlines = (IngredientRecipeInline, TagRecipeInline,)
    list_display = ('name', 'author', 'cooking_time',
                    'id', 'count_favorite', 'pub_date')
    search_fields = ('name', 'author', 'tags')
    empty_value_display = '-пусто-'
    list_filter = ('name', 'author', 'tags')

    def count_favorite(self, obj):
        return Favorite.objects.filter(recipe=obj).count()

    count_favorite.short_description = 'Число добавлений в избранное'
