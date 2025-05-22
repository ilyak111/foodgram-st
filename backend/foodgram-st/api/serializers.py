
from rest_framework import serializers
from django.core.files.base import ContentFile
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError
import base64

from users.models import (
    CustomUser
)
from recipes.models import (
    MyIngredient,
    RecipeIngredient,
    MyRecipe,
    MyShoppingCart,
    MyFavorite
)


class MyIngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = MyIngredient
        fields = ['id', 'measurement_unit', 'name']


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=MyIngredient.objects.all(),
        source='ingredient'
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    amount = serializers.IntegerField(
        min_value=1,
        max_value=100000,
        error_messages={
            'min_value': 'amount должен быть не меньше 1.',
            'max_value': 'amount должен быть не больше 100000.'
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
        current_user = self.context.get('request').user

        if current_user.is_authenticated:
            return obj.authors.filter(user=current_user).exists()
        return False


class MyRecipeSerializer(serializers.ModelSerializer):
    author = CustomUserReadSerializer(read_only=True)
    image = Base64ImageField(required=True)
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    cooking_time = serializers.IntegerField(min_value=1)
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
        model = MyRecipe
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
            ingredient_id = ingredient.get("ingredient").id
            if ingredient_id in ingredient_ids:
                raise ValidationError("Ингредиенты должны быть уникальными.")
            ingredient_ids.append(ingredient_id)

        return ingredients

    def get_is_in_shopping_cart(self, obj):
        current_user = self.context.get('request').user

        if current_user.is_authenticated:
            return MyShoppingCart.objects.filter(
                user=current_user,
                recipe=obj
            ).exists()
        return False

    def create(self, validated_data):
        current_ingredients_data = validated_data.pop('ingredient_recipe')

        current_recipe = MyRecipe.objects.create(**validated_data)
        current_recipe.save()

        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=current_recipe,
                amount=ingredient['amount'],
                ingredient=ingredient['ingredient']
            ) for ingredient in current_ingredients_data
        ])
        return current_recipe

    def update(self, instance, validated_data):
        current_ingredients_data = validated_data.pop(
            'ingredient_recipe',
            None
        )

        instance = super().update(instance, validated_data)
        instance.save()

        if current_ingredients_data is not None:
            instance.ingredients.clear()

            RecipeIngredient.objects.bulk_create([
                RecipeIngredient(
                    recipe=instance,
                    ingredient=ingredient_data['ingredient'],
                    amount=ingredient_data['amount']
                ) for ingredient_data in current_ingredients_data
            ])

        else:
            raise ValidationError(
                'ingredients обязательно для обновления рецепта.'
            )
        return instance

    def get_is_favorited(self, obj):
        current_user = self.context.get('request').user

        if current_user.is_authenticated:
            return MyFavorite.objects.filter(
                user=current_user,
                recipe=obj
            ).exists()
        return False


class SmallRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(allow_null=True)

    class Meta:
        model = MyRecipe
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


class MySubscritionSerializer(serializers.ModelSerializer):
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
        current_user = self.context.get('request').user

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

        recipes_queryset = MyRecipe.objects.filter(author=instance)

        if recipes_limit is not None:
            recipes_queryset = recipes_queryset[:recipes_limit]

        serialized_recipes = SmallRecipeSerializer(recipes_queryset, many=True)
        return serialized_recipes.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
