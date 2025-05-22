from django.contrib import admin
from .models import (
    MyRecipe,
    RecipeIngredient,
    MyFavorite,
    MyShoppingCart
)


class AdminRecipeIngredientInline(admin.TabularInline):
    extra = 1
    model = RecipeIngredient


class AdminMyRecipe(admin.ModelAdmin):
    list_display = ('id', 'name', 'count_recipes_favorites', 'get_username')
    list_filter = ('author',)
    search_fields = ('name', 'author__username')
    inlines = [AdminRecipeIngredientInline]

    def count_recipes_favorites(self, object):
        return object.favorite.count()

    def get_username(self, object):
        return object.user.username


class AdminMyFavorite(admin.ModelAdmin):
    list_display = ['user', 'recipe']
    autocomplete_fields = ['user', 'recipe']


class AdminMyShoppingCart(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    autocomplete_fields = ['user', 'recipe']


admin.site.register(MyRecipe, AdminMyRecipe)
admin.site.register(MyFavorite, AdminMyFavorite)
admin.site.register(MyShoppingCart, AdminMyShoppingCart)
