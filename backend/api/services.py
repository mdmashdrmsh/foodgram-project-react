"""
Дополнительные функции.
"""
from string import hexdigits

from rest_framework.serializers import ValidationError

from recipes.models import IngredientAmount


def is_hex_color(value):
    """Проверяем, может ли значение быть HEX-цветом."""
    if len(value) not in (3, 6):
        raise ValidationError(
            f'{value} не правильной длины ({len(value)}.'
        )
    if not set(value).issubset(hexdigits):
        raise ValidationError(
            f'{value} не шестнадцатеричное.'
        )


def enter_ingredient_amount_in_recipe(recipe, ingredients):
    """
    Записывает вложенные в рецепт ингредиенты.
    Создает объект IngredientAmount, связывающий объекты Recipe и
    Ingredient с указанием количества ('amount') конкретного ингредиента.
    """
    for ingredient in ingredients:
        IngredientAmount.objects.get_or_create(
            recipe=recipe,
            ingredients=ingredient['ingredient'],
            amount=ingredient['amount'],
        )


def check_value_validate(value, klass=None):
    """
    Проверяет корректность переданного значения.
    Если передан класс, проверяет, существует ли объект с переданным obj_id.
    При нахождении объекта создается Queryset[],
    для дальнейшей работы возвращает первое (и единственное) значение.
    """
    if not str(value).isdecimal():
        raise ValidationError(
            f'{value} должно содержать цифру'
        )
    if int(value) <= 0:
        raise ValidationError(
            'Значение должно быть больше 0'
        )
    if klass:
        obj = klass.objects.filter(id=value)
        if not obj:
            raise ValidationError(
                f'{value} не существует'
            )
        return obj[0]
