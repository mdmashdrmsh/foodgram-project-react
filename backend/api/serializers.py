from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (ModelSerializer, SerializerMethodField,
                                        ValidationError)

from recipes.models import Ingredient, Recipe, Tag

from .services import (check_value_validate,
                       enter_ingredient_amount_in_recipe, is_hex_color)

User = get_user_model()


class ShortRecipeSerializer(ModelSerializer):
    """
    Сериализатор для модели Recipe.
    Определен укороченный набор полей для некоторых эндпоинтов.
    """
    class Meta:
        model = Recipe
        fields = 'id', 'name', 'image', 'cooking_time'
        read_only_fields = '__all__',


class UserSerializer(ModelSerializer):
    """Сериализатор для модели User."""
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = 'is_subscribed',

    def get_is_subscribed(self, author):
        """
        Проверка подписан ли текущий пользователь
        на просматриваемого пользователя author.
        """
        user = self.context.get('request').user
        if user.is_anonymous or (user == author):
            return False
        return user.follow.filter(id=author.id).exists()

    def create(self, validated_data):
        """
        Создание нового пользователя с запрошенными
        проверенными полями validated_data
        """
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def validate_username(self, username):
        """
        Проверяет введённый логин username.
        """
        if len(username) < 3:
            raise ValidationError(
                'Длина username допустима от 3 до 150'
            )
        if not username.isalpha():
            raise ValidationError(
                'В username допустимы только буквы.'
            )
        return username.capitalize()


class UserSubscribeSerializer(UserSerializer):
    """
    Сериализатор вывода авторов, на которых подписан текущий пользователь.
    """
    recipes = SerializerMethodField(read_only=True)
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        read_only_fields = '__all__',

    def get_is_subscribed(*args):
        """
        Проверка подписки пользователей.
        Переопределённый метод родительского класса для уменьшения нагрузки,
        так как в текущей реализации всегда вернёт `True`.
        """
        return True

    def get_recipes_count(self, author):
        """
        Показывает общее количество рецептов у каждого автора author.
        """
        return author.recipes.count()

    def get_recipes(self, obj):
        """
        Показывает рецепты авторов в подписках
        """
        request = self.context.get('request')
        recipes = obj.recipes.all()
        limit = request.query_params.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        return ShortRecipeSerializer(recipes, many=True).data


class TagSerializer(ModelSerializer):
    """
    Сериализатор для вывода тэгов.
    """
    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = '__all__',

    def validate_color(self, color):
        """
        Приводит к hex-виду код цвета color.
        """
        color = str(color).strip(' #')
        is_hex_color(color)
        return f'#{color}'


class IngredientSerializer(ModelSerializer):
    """
    Сериализатор для вывода ингредиентов.
    """
    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = '__all__',


class RecipeSerializer(ModelSerializer):
    """
    Сериализатор для рецептов.
    """
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

        read_only_fields = (
            'is_favorite',
            'is_shopping_cart',
        )

    def get_ingredients(self, recipe):
        """
        Получает список ингредиентов для рецепта recipe.
        """
        ingredients = recipe.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recipe__amount')
        )
        return ingredients

    def get_is_favorited(self, obj):
        """
        Проверка, находится ли рецепт в избранном.
        """
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.favorites.filter(id=obj.id).exists()

    def get_is_in_shopping_cart(self, recipe):
        """
        Проверка, находится ли рецепт recipe в списке покупок."""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.shopping_list.filter(id=recipe.id).exists()

    @transaction.atomic
    def validate(self, data):
        """
        Проверка вводных данных data при создании и изменении рецепта.
        """
        name = str(self.initial_data.get('name')).strip()
        tags = self.initial_data.get('tags')
        ingredients = self.initial_data.get('ingredients')
        values_list = (tags, ingredients)

        for value in values_list:
            if not isinstance(value, list):
                raise ValidationError(
                    f'"{value}" должен быть списком "[]"'
                )

        for tag in tags:
            check_value_validate(tag, Tag)

        valid_ingredients = []
        for ing in ingredients:
            ing_id = ing.get('id')
            ingredient = check_value_validate(ing_id, Ingredient)

            amount = ing.get('amount')
            check_value_validate(amount)

            valid_ingredients.append(
                {
                    'ingredient': ingredient,
                    'amount': amount,
                }
            )
        if len(valid_ingredients) != len(
               set(obj['ingredient'] for obj in valid_ingredients)):
            raise ValidationError(
                'Нельзя добавить один ингредиент более одного раза'
            )
        data['name'] = name.capitalize()
        data['tags'] = tags
        data['ingredients'] = valid_ingredients
        data['author'] = self.context.get('request').user
        return data

    @transaction.atomic
    def create(self, validated_data):
        """
        Создание рецепта.
        """
        image = validated_data.pop('image')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(image=image, **validated_data)
        recipe.tags.set(tags)
        enter_ingredient_amount_in_recipe(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, recipe, validated_data):
        """
        Обновление рецепт.
        """
        tags = validated_data.get('tags')
        ingredients = validated_data.get('ingredient')

        recipe.image = validated_data.get(
            'image', recipe.image)
        recipe.name = validated_data.get(
            'name', recipe.name)
        recipe.text = validated_data.get(
            'text', recipe.text)
        recipe.cooking_time = validated_data.get(
            'cooking_time', recipe.cooking_time)

        if tags:
            recipe.tags.clear()
            recipe.tags.set(tags)

        if ingredients:
            recipe.ingredients.clear()
            enter_ingredient_amount_in_recipe(recipe, ingredients)

        recipe.save()
        return recipe
