from django.urls import path, include
from rest_framework.authtoken import views
from rest_framework.routers import DefaultRouter

from api.views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    ShoppingCartViewSet,
    CreateUserView,
    DownloadCartView,
    FavoriteViewSet,
    FollowViewSet,
)


app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register('users', CreateUserView, basename='users')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('users/subscriptions/',
         FollowViewSet.as_view({'get': 'list'}), name='subscriptions'),
    path('recipes/download_shopping_cart/',
         DownloadCartView.as_view(), name='dowload_shopping_cart'),
    path('users/<users_id>/subscribe/',
         FollowViewSet.as_view({'post': 'create',
                                'delete': 'delete'}), name='subscribe'),
    path('recipes/<recipes_id>/favorite/',
         FavoriteViewSet.as_view({'post': 'create',
                                  'delete': 'delete'}), name='favorite'),
    path('recipes/<recipes_id>/shopping_cart/',
         ShoppingCartViewSet.as_view({'post': 'create',
                                      'delete': 'delete'}), name='cart'),
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('api-token-auth/', views.obtain_auth_token),
]
