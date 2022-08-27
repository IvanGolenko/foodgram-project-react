from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ADMIN = 'admin'
    USER = 'user'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']
    ROLES = [
        (ADMIN, 'admin'),
        (USER, 'user'),
    ]

    username = models.CharField(
        verbose_name='Уникальное имя',
        help_text='Введите уникальное имя пользователя',
        unique=True,
        null=False,
        max_length=150,
    )
    email = models.EmailField(
        verbose_name='Адрес эл.почты',
        unique=True,
        null=False,
        max_length=150,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        null=False,
        max_length=150,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
    )
    role = models.CharField(
        verbose_name='Роль',
        max_length=100,
        choices=ROLES,
        default=USER
    )

    class Meta:
        ordering = ['pk']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    @property
    def is_admin(self):
        return self.role == self.ADMIN


class Follower(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
        blank=False,
        null=False,
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
        blank=False,
        null=False,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_subscribe'
            ),
        ]

    def __str__(self):
        return f'{self.user} {self.following}'
