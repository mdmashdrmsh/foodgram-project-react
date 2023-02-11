from colorfield.fields import ColorField
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    MaxLengthValidator, MinLengthValidator)
from django.db import models

from users.models import User


class Tag(models.Model):
    """
    Тэги для рецептов
    """
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Тэг',
    )
    color = ColorField(
        default='#FF0000',
        verbose_name='Цветовой HEX-код',
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Слаг тэга',
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name', )

    def __str__(self):
        return f'{self.name} (цвет: {self.color})'


class Ingredient(models.Model):
    """
    Ингредиенты для рецепта
    """
    name = models.CharField(
        max_length=200,
        verbose_name='Ингредиент',
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единицы измерения',
    )

    class Meta:
        unique_together = ('name', 'measurement_unit')
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name', ]

    def __srt__(self):
        return f'{self.name}, {self.measurement_unit}.'


class Recipe(models.Model):
    """
    Модель рецепта
    """
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта',
        help_text='Введите название рецепта',
    )
    image = models.ImageField(
        upload_to='recipe_pictures/',
        blank=True,
        null=True,
        verbose_name='Изображение блюда',
    )
    text = models.TextField(
        validators=(
            MinLengthValidator(
                10,
                'Дайте краткое описание рецепта'
            ),
            MaxLengthValidator(
                1000,
                'Слишком длинное описание рецепта'
            ),
        ),
        verbose_name='Текстовое описание рецепта',
        help_text='Введите текстовое описание рецепта',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэг',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='recipes.IngredientAmount',
        verbose_name='Ингредиенты блюда',
        related_name='recipes',
    )
    cooking_time = models.PositiveSmallIntegerField(
        default=1,
        validators=(
            MinValueValidator(
                1,
                'За такое время блюдо не приготовить'
            ),
            MaxValueValidator(
                600,
                'Слишком долго готовить'
            ),
        ),
        verbose_name='Время приготовления в минутах',
    )
    create_data = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )
    is_favorite = models.ManyToManyField(
        User,
        related_name='favorites',
        verbose_name='Избранное',
    )
    is_in_shopping_list = models.ManyToManyField(
        User,
        related_name='shopping_list',
        verbose_name='Список покупок',
    )

    class Meta:
        ordering = ['-create_data', ]
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientAmount(models.Model):
    """
    Количество ингредиентов в конкретном рецепте
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient',
        verbose_name='В каких рецептах'
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Связанные ингредиенты',
    )
    amount = models.PositiveSmallIntegerField(
        default=1,
        validators=(
            MinValueValidator(
                1, 'Количество ингредиента должно быть больше 0'
            ),
            MaxValueValidator(
                1000, 'Слишком много для любого блюда'
            ),
        ),
        verbose_name='Количество',
    )

    class Meta:
        ordering = ('recipe', )
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredients', ),
                name='ingredient_amount'
            ),
        )

    def __str__(self):
        return f'{self.amount} {self.ingredients}'
