from django.contrib import admin

from recipes.models import (
    Ingredient, IngredientInRecipe, Favorite,
    Recipe, ShoppingCart, Tag, TagInRecipe,
)


class IngredientAdmin(admin.ModelAdmin):
    list_filter = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    list_filter = ('name', 'author', 'tags')
    list_display = ['name', 'image', 'cooking_time',
                    'author', 'text', 'pub_date', 'favorited_count']

    @staticmethod
    def favorited_count(obj):
        return obj.favorite_set.count()


admin.site.register(Favorite)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientInRecipe)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShoppingCart)
admin.site.register(Tag)
admin.site.register(TagInRecipe)
