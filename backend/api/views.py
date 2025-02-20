from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, serializers
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from djoser.views import UserViewSet
from djoser.permissions import CurrentUserOrAdmin

from recipes.models import (Tag, Recipe, Ingredient, Favorite, ShoppingCart)
from users.models import User, Subscription
from .serializers import (TagSerializer,
                          SpecialRecipeSerializer,
                          IngredientSerializer,
                          FoodgramUserSerializer,
                          FoodgramCreateUserSerializer,
                          SubscriptionSerializer,
                          RecipeSerializer, UserAvatarSerializer)
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .filters import NameFilter, RecipeFilter


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly | IsAdminOrReadOnly,)
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True,
            methods=['post'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        Favorite.objects.create(user=request.user, recipe=recipe)
        serializer = SpecialRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        favorite = Favorite.objects.filter(user=request.user, recipe__id=pk)
        if favorite.exists():
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['post'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if ShoppingCart.objects.filter(user=request.user,
                                       recipe=recipe).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        serializer = SpecialRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        cart = ShoppingCart.objects.filter(user=request.user, recipe__id=pk)
        if cart.exists():
            cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['get'],
            url_path='get-link')
    def get_link(self, request, pk):
        get_object_or_404(self.get_queryset(), pk=pk)
        return Response({
            'short-link': request.build_absolute_uri(
                reverse('short-link', args=(pk,))
            )
        })

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        ingredients = Ingredient.objects.filter(
            recipe__recipe__shopping_cart__user=user).values(
            'name',
            'measurement_unit').annotate(amount=Sum('recipe__amount'))
        shopping_list = ['Список покупок.']
        for ingredient in ingredients:
            shopping_list += [
                f'{ingredient["name"]}'
                f'({ingredient["measurement_unit"]}):'
                f'{ingredient["amount"]}']
        filename = f'{user.username}_shopping_list.txt'
        result_list = '\n'.join(shopping_list)
        response = HttpResponse(result_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = DjangoFilterBackend,
    filterset_class = NameFilter
    pagination_class = None


class FoodgramUserViewSet(UserViewSet):
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return FoodgramUserSerializer
        return FoodgramCreateUserSerializer

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    @action(
        ['put'], detail=False, url_path='me/avatar',
        permission_classes=[CurrentUserOrAdmin]
    )
    def me_avatar(self, request):
        user = request.user
        serializer = UserAvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @me_avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        ['get'], detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        subscribers = User.objects.filter(
            subscribers__user=request.user
        )
        pages = self.paginate_queryset(subscribers)
        serializer = SubscriptionSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        ['post'], detail=True, url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        author = self.get_object()
        if request.user == author:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя."
            )
        _, created = Subscription.objects.get_or_create(
            user=request.user, author=author
        )
        if not created:
            raise serializers.ValidationError(
                {'subscribe': f'Вы уже подписаны на "{author}"'}
            )
        subscribing_data = SubscriptionSerializer(
            author, context={'request': request}
        ).data
        return Response(subscribing_data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        author = self.get_object()
        get_object_or_404(
            Subscription, user=request.user, author=author
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
