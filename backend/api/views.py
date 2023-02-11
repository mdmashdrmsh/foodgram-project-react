from datetime import datetime as dt
from urllib.parse import unquote

from django.contrib.auth import get_user_model
from django.db.models import F, Sum
from django.http.response import HttpResponse
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import Ingredient, IngredientAmount, Recipe, Tag

from .mixins import AddDelViewMixin
from .paginators import PageLimitPagination
from .permissions import IsAdminOrReadOnly, IsAuthorStaffOrReadOnly
from .serializers import (IngredientSerializer, RecipeSerializer,
                          ShortRecipeSerializer, TagSerializer,
                          UserSubscribeSerializer)

User = get_user_model()


class UserViewSet(DjoserUserViewSet, AddDelViewMixin):
    """
    Работает с пользователями.
    ViewSet для работы с пользователями - вывод, регистрация.
    Для авторизованных пользователей - возможность
    подписаться на автора рецепта.
    """
    pagination_class = PageLimitPagination
    add_serializer = UserSubscribeSerializer

    @action(methods=('GET', 'POST', 'DELETE',), detail=True)
    def subscribe(self, request, id):
        """Создаёт/удалет связь между пользователями.
        */user/<int:id>/subscribe/.
        """
        return self.add_remove_relation(id, 'follow_M2M')

    @action(methods=('get',), detail=False)
    def subscriptions(self, request):
        """Список подписок пользоваетеля.
        */user/<int:id>/subscribtions/.
        """
        user = self.request.user
        if user.is_anonymous:
            return Response(status=HTTP_401_UNAUTHORIZED)
        authors = user.follow.all()
        pages = self.paginate_queryset(authors)
        serializer = UserSubscribeSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(ReadOnlyModelViewSet):
    """
    Работает с тэгами.
    Изменение и создание тэгов разрешено только админам.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class IngredientViewSet(ReadOnlyModelViewSet):
    """
    Работает с ингредиентами.
    Изменение и создание ингредиентов разрешено только админам.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)

    def get_queryset(self):
        """
        Получает queryset в соответствии с параметрами запроса.
        Ищет объекты по совпадению в начале названия,
        также добавляются результаты по совпадению в середине.
        Прописные буквы преобразуются в строчные,
        так как все ингредиенты в базе даны в нижнем регистре.
        """
        name = self.request.query_params.get('name')
        queryset = self.queryset
        if name:
            if name[0] == '%':
                name = unquote(name)
            name = name.lower()
            stw_queryset = list(queryset.filter(name__startswith=name))
            cnt_queryset = queryset.filter(name__contains=name)
            stw_queryset.extend(
                [i for i in cnt_queryset if i not in stw_queryset]
            )
            queryset = stw_queryset
        return queryset


class RecipeViewSet(ModelViewSet, AddDelViewMixin):
    """
    Работает с рецептами.
    Вывод, создание, редактирование, добавление/удаление
    в избранное и список покупок.
    Отправка текстового файла со списком покупок.
    Для авторизованных пользователей - возможность добавить
    рецепт в избранное и в список покупок.
    Изменять рецепт может только автор или админ.
    """
    queryset = Recipe.objects.select_related('author')
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorStaffOrReadOnly,)
    pagination_class = PageLimitPagination
    add_serializer = ShortRecipeSerializer

    def get_queryset(self):
        """
        Фильтрация в соответствии с параметрами запроса.
        """
        queryset = self.queryset
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(
                tags__slug__in=tags).distinct()

        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author=author)

        # Фильтры ниже - только для авторизованного пользователя
        user = self.request.user
        if user.is_anonymous:
            return queryset

        is_in_shopping = self.request.query_params.get('is_in_shopping_cart')
        if is_in_shopping in ('1', 'true',):
            queryset = queryset.filter(is_in_shopping_list=user.id)
        elif is_in_shopping in ('0', 'false',):
            queryset = queryset.exclude(is_in_shopping_list=user.id)

        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited in ('1', 'true',):
            queryset = queryset.filter(is_favorite=user.id)
        if is_favorited in ('0', 'false',):
            queryset = queryset.exclude(is_favorite=user.id)

        return queryset

    @action(methods=('GET', 'POST', 'DELETE',), detail=True)
    def favorite(self, request, pk):
        """
        Добавляет/удаляет рецепт в 'избранное'
        """
        return self.add_remove_relation(pk, 'is_favorite_M2M')

    @action(methods=('GET', 'POST', 'DELETE',), detail=True)
    def shopping_cart(self, request, pk):
        """
        Добавляет/удаляет рецепт в 'список покупок'
        """
        return self.add_remove_relation(pk, 'shopping_cart_M2M')

    @action(methods=('get',), detail=False)
    def download_shopping_cart(self, request):
        """
        Загружает файл *.txt со списком покупок
        """
        TIME_FORMAT = '%d/%m/%Y %H:%M'
        user = self.request.user
        if not user.shopping_list.exists():
            return Response(status=HTTP_400_BAD_REQUEST)
        ingredients = IngredientAmount.objegicts.filter(
            recipe__in=(user.shopping_list.values('id'))
        ).values(
            name=F('ingredients__name'),
            measure=F('ingredients__measurement_unit')
        ).annotate(amount=Sum('amount'))

        filename = f'{user.username}_shopping_list.txt'
        shopping_list = (f'Список покупок для пользователя '
                         f'{user.first_name}:\n\n')
        ingredients_set = {}
        for ing in ingredients:
            name = ing['name']
            amount = ing['amount']
            measure = ing['measure']
            if name not in ingredients_set:
                ingredients_set[name] = {
                    'amount': amount,
                    'measure': measure,
                }
            else:
                ingredients_set[name]['amount'] += amount

        for name in ingredients_set:
            shopping_list += (f"{name}: "
                              f"{ingredients_set[name]['amount']}"
                              f"{ingredients_set[name]['measure']}\n")

        shopping_list += (
            f'\nДата составления {dt.now().strftime(TIME_FORMAT)}.'
            '\n\nMade in Foodgram 2022 (c)'
        )

        response = HttpResponse(
            shopping_list, content_type='text.txt; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
