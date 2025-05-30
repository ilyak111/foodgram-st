
from rest_framework import serializers
from django.core.files.base import ContentFile
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError
import base64

from users.models import (
    CustomUser
)
from recipes.models import (
    Ingredient,
    RecipeIngredient,
    Recipe,
    ShoppingCart,
    Favorite
)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ['id', 'measurement_unit', 'name']


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    amount = serializers.IntegerField(
        min_value=RecipeIngredient.MIN_AMOUNT,
        max_value=RecipeIngredient.MAX_AMOUNT,
        error_messages={
            'min_value': f'amount должен быть не меньше {RecipeIngredient.MIN_AMOUNT}.',
            'max_value': f'amount должен быть не больше {RecipeIngredient.MAX_AMOUNT}.'
        }
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'recipe', 'amount', 'name']
        read_only_fields = ['id', 'recipe']

    def to_representation(self, instance):

        representation = super().to_representation(instance)
        current_ingredient = instance.ingredient
        return {
            'id': current_ingredient.id,
            'measurement_unit': current_ingredient.measurement_unit,
            'name': current_ingredient.name,
            'amount': representation['amount'],
        }


class CustomUserWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'id', 'username', 'email', 'first_name',
            'last_name', 'password'
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomUserReadSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = CustomUser

        fields = (
            'id', 'username', 'email', 'first_name',
            'avatar', 'is_subscribed', 'last_name'
        )

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user

        if current_user.is_authenticated:
            return obj.authors.filter(user=current_user).exists()
        return False


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserReadSerializer(read_only=True)
    image = Base64ImageField(required=True)
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    cooking_time = serializers.IntegerField(
        min_value=Recipe.MIN_COOKING_TIME,
        max_value=Recipe.MAX_COOKING_TIME,
        error_messages={
            'min_value': f'cooking_time должен быть не меньше {Recipe.MIN_COOKING_TIME}.',
            'max_value': f'cooking_time должен быть не больше {Recipe.MAX_COOKING_TIME}.'
        }
    )
    is_favorited = serializers.SerializerMethodField(
        required=False
    )
    ingredients = IngredientRecipeSerializer(
        source='ingredient_recipe',
        many=True
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        required=False
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'ingredients', 'is_favorited',
            'text', 'cooking_time', 'author', 'is_in_shopping_cart'
        )
        read_only_fields = (
            'is_in_shopping_cart', 'is_favorited', 'author'
        )

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                "Не заполнено изображение."
            )
        return value

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise ValidationError('Ингредиенты отсутствуют.')

        ingredient_ids = []
        for ingredient in ingredients:
            ingredient_id = ingredient["ingredient"].id
            if ingredient_id in ingredient_ids:
                raise ValidationError("Ингредиенты должны быть уникальными.")
            ingredient_ids.append(ingredient_id)

        return ingredients

    def get_is_in_shopping_cart(self, obj):
        current_user = self.context['request'].user

        if current_user.is_authenticated:
            # return ShoppingCart.objects.filter(
            #     user=current_user,
            #     recipe=obj
            # ).exists()
            return obj.shopping_cart.filter(user=current_user).exists()
        return False

    def create(self, validated_data):
        current_ingredients_data = validated_data.pop('ingredient_recipe')

        current_recipe = Recipe.objects.create(**validated_data)
        current_recipe.save()

        self._create_ingredients(current_recipe, current_ingredients_data)
        return current_recipe

    def update(self, instance, validated_data):
        current_ingredients_data = validated_data.pop(
            'ingredient_recipe',
            None
        )

        instance = super().update(instance, validated_data)
        instance.save()

        if current_ingredients_data is None:
            raise ValidationError(
                'ingredients обязательно для обновления рецепта.'
            )
        
        instance.ingredients.clear()
        self._create_ingredients(instance, current_ingredients_data)
        return instance

    def get_is_favorited(self, obj):
        current_user = self.context['request'].user

        if current_user.is_authenticated:
            # return Favorite.objects.filter(
            #     user=current_user,
            #     recipe=obj
            # ).exists()
            return obj.favorite.filter(user=current_user).exists()
        return False
    
    def _create_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            ) for ingredient_data in ingredients_data
        ])

class SmallRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(allow_null=True)

    class Meta:
        model = Recipe
        fields = ('id', 'image', 'name', 'cooking_time')


class CustomUserAvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(
        write_only=True,
        allow_null=False
    )

    class Meta:
        model = CustomUser
        fields = ['avatar']

    def validate_avatar(self, avatar_data):
        if not isinstance(avatar_data, str) or ';base64,' not in avatar_data:
            raise serializers.ValidationError('Некорректный аватар.')

        header, data = avatar_data.split(';base64,', 1)
        file_extension = header.split('/')[-1]

        file = base64.b64decode(data)

        return ContentFile(
            content=file,
            name=f'avatar.{file_extension}'
        )

    def update(self, instance, validated_data):
        if 'avatar' not in validated_data:
            raise serializers.ValidationError(
                'avatar обязателен для метода update.'
            )

        instance.avatar = validated_data['avatar']
        instance.save()
        return instance


class SubscritionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = Base64ImageField(required=False, allow_null=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id', 'username', 'first_name', 'avatar',
            'email', 'last_name', 'recipes', 'is_subscribed',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user

        if current_user.is_authenticated:
            return obj.authors.filter(user=current_user).exists()
        return False

    def get_recipes(self, instance):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')

        if limit and limit.isdigit():
            recipes_limit = int(limit)
        else:
            recipes_limit = None

        # recipes_queryset = Recipe.objects.filter(author=instance)
        recipes_queryset = instance.recipes.all()

        if recipes_limit is not None:
            recipes_queryset = recipes_queryset[:recipes_limit]

        serialized_recipes = SmallRecipeSerializer(recipes_queryset, many=True)
        return serialized_recipes.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
