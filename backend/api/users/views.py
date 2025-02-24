from django.shortcuts import get_object_or_404
from rest_framework import status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from djoser.views import UserViewSet
from djoser.permissions import CurrentUserOrAdmin

from users.models import User, Subscription
from .serializers import (FoodgramUserSerializer,
                          FoodgramCreateUserSerializer,
                          UserAvatarSerializer)
from ..recipes.serializers import SubscriptionSerializer


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
