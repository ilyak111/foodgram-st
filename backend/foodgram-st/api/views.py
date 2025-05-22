from rest_framework import filters
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .serializers import (
    CustomUserReadSerializer,
    CustomUserWriteSerializer,
    CustomUserAvatarSerializer,
    MySubscritionSerializer,
    MyRecipeSerializer,
    SmallRecipeSerializer,
    MyIngredientSerializer
)
from api.permissions import CustomPermission
from djoser.views import UserViewSet as DjoserUser
from rest_framework import status, viewsets, permissions
import django_filters
from recipes.models import (
    MyRecipe,
    MyShoppingCart,
    MyFavorite,
    RecipeIngredient
)
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse
from users.models import MySubscribe, CustomUser
from ingredients.models import MyIngredient
from rest_framework.pagination import PageNumberPagination


class MyPaginator(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 10


class RecipeFilter(django_filters.FilterSet):
    is_in_shopping_cart = django_filters.CharFilter(
        method='filter_is_in_shopping_cart'
    )
    is_favorited = django_filters.CharFilter(
        method='filter_is_favorited'
    )

    class Meta:
        model = MyRecipe
        fields = ['is_in_shopping_cart', 'is_favorited', 'author']

    def filter_is_favorited(self, queryset, name, value):
        current_user = self.request.user
        if not current_user.is_authenticated:
            return queryset

        if value == "1":
            return queryset.filter(favorite__user=current_user)
        elif value == "0":
            return queryset.exclude(favorite__user=current_user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):

        current_user = self.request.user
        if not current_user.is_authenticated:
            return queryset

        if value == '1':
            return queryset.filter(shopping_cart__user=current_user)
        elif value == '0':
            return queryset.exclude(shopping_cart__user=current_user)
        return queryset


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = MyIngredient.objects.all()
    http_method_names = ['get']
    serializer_class = MyIngredientSerializer
    filterset_fields = ['name']
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = MyRecipe.objects.all()
    serializer_class = MyRecipeSerializer
    filter_backends = [DjangoFilterBackend]
    pagination_class = MyPaginator
    permission_classes = [CustomPermission]
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_link = f'(https://foodgram.ru/{recipe.pk})'
        return Response({'short-link': short_link}, status=status.HTTP_200_OK,)

    @staticmethod
    def handle_recipe(
        request, serializer_class, model_class, recipe_id
    ):
        current_recipe = get_object_or_404(MyRecipe, pk=recipe_id)
        current_user = request.user

        if request.method == 'POST':
            recipe_exists = model_class.objects.filter(
                recipe=current_recipe,
                user=current_user
            ).exists()
            if recipe_exists:
                return Response(
                    {
                        'Нельзя добавить один рецепт несколько раз'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = serializer_class(
                current_recipe,
                context={'request': request}
            )
            model_class.objects.create(
                user=current_user,
                recipe=current_recipe
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted_count, _ = model_class.objects.filter(
            user=current_user, recipe=current_recipe
        ).delete()

        if deleted_count == 0:
            return Response(
                {'Рецепта нет в списке'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['delete', 'post'],
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        return self.handle_recipe(
            request, SmallRecipeSerializer, MyFavorite, pk
        )

    @action(detail=True, methods=['delete', 'post'],
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self.handle_recipe(
            request, SmallRecipeSerializer, MyShoppingCart, pk
        )

    @action(
        detail=False,
        permission_classes=[IsAuthenticated],
        methods=['get']
    )
    def download_shopping_cart(self, request):
        shopping_cart_items = request.user.shopping_cart.all()

        if not shopping_cart_items.exists():
            return Response({'Корзина пуста.'}, status=404)

        shopping_cart = {}
        for item in shopping_cart_items:
            current_recipe = item.recipe
            ingredients = RecipeIngredient.objects.filter(
                recipe=current_recipe
            )

            for item in ingredients:
                if item.ingredient not in shopping_cart:
                    shopping_cart[item.ingredient] = item.amount
                else:
                    shopping_cart[item.ingredient] += item.amount

        shopping_cart_list = []
        shopping_cart_list.extend(
            f'{ingredient}: {amount} {ingredient.measurement_unit}'
            for ingredient, amount in shopping_cart.items()
        )

        return FileResponse(
            "\n".join(shopping_cart_list),
            as_attachment=True,
            filename="shopping_list.txt",
            content_type="text/plain; charset=utf-8",
        )


class UserViewSet(DjoserUser):
    queryset = CustomUser.objects.all()
    pagination_class = MyPaginator

    def get_serializer_class(self):
        if self.action in ["list", "retrieve", "me"]:
            return CustomUserReadSerializer
        return CustomUserWriteSerializer

    def create(self, request):
        current_serializer = self.get_serializer_class()(
            context={'request': request},
            data=request.data
        )

        if current_serializer.is_valid():
            current_serializer.save()
            user_data = current_serializer.data
            user_data.pop('avatar', None)
            user_data.pop('is_subscribed', None)
            return Response(user_data, status=201)
        else:
            return Response(
                {'Некорректные данные пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        subscribes = MySubscribe.objects.filter(
            user=request.user).select_related('author')
        authors = [sub.author for sub in subscribes]
        pages = self.paginate_queryset(authors)

        serializer = MySubscritionSerializer(
            pages,
            context={'request': request},
            many=True
        )

        return self.get_paginated_response(serializer.data)

    @action(
        methods=["delete", "post"],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        subscriber = request.user
        author = self.get_object()

        if request.method == "POST":

            subscribtion, create = MySubscribe.objects.get_or_create(
                author=author,
                user=subscriber
            )

            if author == subscriber:
                return Response(
                    {"Невозможно подписаться на себя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not create:
                return Response(
                    {
                        "Вы уже подписаны на этого пользователя "
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = MySubscritionSerializer(
                subscriber,
                context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        try:
            get_object_or_404(
                MySubscribe,
                author=author,
                user=subscriber
            ).delete()
        except Exception:
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        serializer_class=CustomUserAvatarSerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=False,
        methods=['delete', 'put'],
        url_path='me/avatar'
    )
    def avatar(self, request):
        current_user = request.user
        if not CustomUser.objects.filter(id=current_user.id).exists():
            return Response(
                'Пользователь не найден.',
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == 'DELETE':
            current_user.avatar.delete(save=False)
            current_user.save()
            return Response(
                {'Аватар удален.'},
                status=status.HTTP_204_NO_CONTENT
            )
        current_serializer = CustomUserAvatarSerializer(
            current_user,
            data=request.data,
            context={'request': request}
        )
        if current_serializer.is_valid():
            current_serializer.save()
            return Response(
                {'avatar': current_user.avatar.url}
            )
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['post'],
        detail=False
    )
    def set_password(self, request):
        current_user = request.user
        request = request.data
        current_password = request.get('current_password')
        new_password = request.get('new_password')

        if not current_user.check_password(current_password):
            return Response(
                {'Неверный пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        current_user.set_password(new_password)
        current_user.save()
        return Response(
            {'Пароль успешно изменен'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        permission_classes=[IsAuthenticated],
        detail=False,
        methods=['get']
    )
    def me(self, request):
        current_user = request.user
        current_serializer = self.get_serializer_class()(
            current_user,
            context={'request': request}
        )
        return Response(current_serializer.data, status=status.HTTP_200_OK)
