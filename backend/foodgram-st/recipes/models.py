from users.models import CustomUser
from django.core.validators import MaxValueValidator
from ingredients.models import MyIngredient
from django.db import models


class MyRecipe(models.Model):
    name = models.CharField(
        blank=False,
        max_length=100,
        verbose_name='Название рецепта'
    )
    author = models.ForeignKey(
        CustomUser,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    text = models.TextField(
        blank=False,
        verbose_name='Краткое описание рецепта'
    )
    cooking_time = models.IntegerField(
        blank=False,
        verbose_name='Время приготовления рецепта',
        validators=[MaxValueValidator(120)]
    )
    ingredients = models.ManyToManyField(
        MyIngredient,
        through='recipes.RecipeIngredient',
        blank=False,
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    image = models.ImageField(
        blank=True,
        upload_to='images/recipes',
        verbose_name='Фотография рецепта',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    amount = models.IntegerField(
        verbose_name='Количество ингредиента',
        validators=[MaxValueValidator(100000)]
    )
    recipe = models.ForeignKey(
        MyRecipe,
        verbose_name='Рецепт',
        related_name='ingredient_recipe',
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        MyIngredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
        related_name='ingredient_recipe'
    )

    class Meta:
        verbose_name = 'Сопоставление рецепта и ингредиента'


class MyFavorite(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorite'
    )
    recipe = models.ForeignKey(
        MyRecipe,
        verbose_name='Любимый рецепт',
        on_delete=models.CASCADE,
        related_name='favorite'
    )

    class Meta:
        verbose_name = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_myfavorite_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user} хранит в избранном {self.recipe}'


class MyShoppingCart(models.Model):
    recipe = models.ForeignKey(
        MyRecipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт в списке покупок',
        related_name='shopping_cart'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_cart'
    )

    class Meta:
        verbose_name = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_myshopping-cart_user_recipe'
            )
        ]
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'{self.user} хранит в списке покупок {self.recipe}'
