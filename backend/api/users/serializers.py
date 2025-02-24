from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.exceptions import ValidationError
from drf_extra_fields.fields import Base64ImageField

from users.models import User


class FoodgramUserSerializer(ModelSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'password', 'avatar')
        read_only_fields = ('is_subscribed',)
        extra_kwargs = {'password': {'write_only': True}}

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user.is_anonymous:
            return user.subscriptions.filter(author=obj).exists()
        return False


class FoodgramCreateUserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserAvatarSerializer(ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class SubscriptionSerializer(FoodgramUserSerializer):
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if user.subscriptions.filter(author=author).exists():
            raise ValidationError(
                'Нельзя подписаться на автора дважды'
            )
        if user == author:
            raise ValidationError(
                'Нельзя подписаться на самого себя'
            )
        return data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
