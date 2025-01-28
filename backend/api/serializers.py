from django.db import transaction
from django.db.models import F

from rest_framework.serializers import (ModelSerializer, 
                                        SerializerMethodField, ReadOnlyField)
from rest_framework.exceptions import ValidationError
from drf_extra_fields.fields import Base64ImageField

from recipes.models import Tag, Recipe, Ingredient, RecipeIngredient
from users.models import User, Subscription


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id', 'name', 'measurement_unit')


class CustomUserSerializer(ModelSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'password')
        read_only_fields = ('is_subscribed',)
        extra_kwargs = {'password': {'write_only': True}}

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user.is_anonymous:
            return user.subscription.filter(author=obj).exists()
        return False


class CustomCreateUserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class RecipeSerializer(ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    image = Base64ImageField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')
        read_only_fields = ('is_favorited', 'is_in_shopping_cart',)

    def get_ingredients(self, obj):
        recipe = obj
        ingredients = recipe.ingredients.values(
            'id',
            'name',
            'measurement_unit')
        return ingredients

    def get_is_favorited(self, obj):
        user = self.context.get('view').request.user
        return user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('view').request.user
        return user.shopping_cart.filter(recipe=obj).exists()

    def validate(self, data):
        tags_ids = self.initial_data.get('tags')
        if not tags_ids:
            raise ValidationError('Необходимо указать хотя бы один тег')
        tags = Tag.objects.filter(id__in=tags_ids)
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise ValidationError('Необходимо указать хотя бы один ингредиент')
        valid_ingredients = {}
        for ingredient in ingredients:
            valid_ingredients[ingredient['id']] = int(ingredient['amount'])
            if int(ingredient['amount']) <= 0:
                raise ValidationError(
                    'Количество ингредиента должно быть больше нуля')
        ingredient_objects = (Ingredient.objects.filter(
            pk__in=valid_ingredients))
        for ingredient_object in ingredient_objects:
            valid_ingredients[ingredient_object.pk] = (
                ingredient_object, valid_ingredients[ingredient_object.pk])
        data.update({'tags': tags,
                     'ingredients': valid_ingredients,
                     'author': self.context.get('request').user})
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                ingredient=ingredient_data,
                recipe=recipe,
                amount=amount
            ) for ingredient_data, amount in ingredients.values()])
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                ingredient=ingredient_data,
                recipe=instance,
                amount=amount
            ) for ingredient_data, amount in ingredients.values()])
        instance.save()
        return instance


class SpecialRecipeSerializer(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(CustomUserSerializer):
    recipes = SpecialRecipeSerializer(many=True, read_only=True)
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if Subscription.objects.filter(user=user, author=author).exists():
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
