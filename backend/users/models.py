from django.db import models
from django.contrib.auth.models import AbstractUser

MAX_LENGTH_CHAR_FIELD = 150


class User(AbstractUser):
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    username = models.CharField(
        max_length=MAX_LENGTH_CHAR_FIELD, 
        unique=True,
        verbose_name='Логин'
    )
    email = models.EmailField(
        max_length=256, 
        unique=True,
        verbose_name='Электронная почта'
    )
    password = models.CharField(
        max_length=MAX_LENGTH_CHAR_FIELD,
        verbose_name='Пароль'
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH_CHAR_FIELD,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_CHAR_FIELD,
        verbose_name='Фамилия'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscriptions(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='subscriptions_unique')]

    def __str__(self):
        return f'Подписка {self.user} на {self.author}'
