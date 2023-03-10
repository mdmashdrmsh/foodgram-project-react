from django.contrib import admin
from django.contrib.admin import TabularInline, register

from .models import Ingredient, IngredientAmount, Recipe, Tag

EMPTY_VALUE_DISPLAY = 'Значение не задано'


class IngredientInline(TabularInline):
    model = IngredientAmount
    extra = 2


@register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'color',
        'slug',
    )
    search_fields = (
        'name',
        'color',
    )

    save_on_top = True
    empty_value_display = EMPTY_VALUE_DISPLAY


@register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = (
        'name',
    )
    list_filter = (
        'name',
    )

    save_on_top = True
    empty_value_display = EMPTY_VALUE_DISPLAY


@register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
    )
    fields = (
        ('name', 'cooking_time',),
        ('author', 'tags',),
        ('text',),
        ('image',),
    )
    raw_id_fields = ('author',)
    search_fields = (
        'name',
        'author',
    )
    list_filter = (
        'name',
        'author__username',
    )

    inlines = (IngredientInline,)
    save_on_top = True
    empty_value_display = EMPTY_VALUE_DISPLAY
