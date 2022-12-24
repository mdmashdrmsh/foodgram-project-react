from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Модель пользователя
    """
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Логин'
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Адрес электронной почты'
    )
    first_name = models.CharField(
        max_length=255,
        null=True,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=255,
        null=True,
        verbose_name='Фамилия'
    )
    follow = models.ManyToManyField(
        to='self',
        symmetrical=False,
        related_name='followers',
        verbose_name='Подписка',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username
