from rest_framework import routers
from django.urls import path, include
from api.views import RecipeViewSet, IngredientViewSet, UserViewSet

router = routers.DefaultRouter()
router.register(
    'recipes',
    RecipeViewSet,
    basename='recipes'
)
router.register(
    'ingredients',
    IngredientViewSet,
)
router.register(
    'users',
    UserViewSet,
)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken'))
]
