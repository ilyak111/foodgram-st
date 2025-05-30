from django.contrib import admin
from .models import (
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart
)


class AdminRecipeIngredientInline(admin.TabularInline):
    extra = 1
    model = RecipeIngredient


class AdminRecipe(admin.ModelAdmin):
    list_display = ('id', 'name', 'count_recipes_favorites', 'get_username')
    list_filter = ('author',)
    search_fields = ('name', 'author__username')
    inlines = [AdminRecipeIngredientInline]

    def count_recipes_favorites(self, object):
        return object.favorite.count()

    def get_username(self, object):
        return object.user.username


class AdminFavorite(admin.ModelAdmin):
    list_display = ['user', 'recipe']
    autocomplete_fields = ['user', 'recipe']


class AdminShoppingCart(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    autocomplete_fields = ['user', 'recipe']


admin.site.register(Recipe, AdminRecipe)
admin.site.register(Favorite, AdminFavorite)
admin.site.register(ShoppingCart, AdminShoppingCart)
