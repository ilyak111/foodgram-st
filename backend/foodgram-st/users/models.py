from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class CustomUser(AbstractUser):
    username = models.CharField(
        'Логин пользователя',
        max_length=128,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message=(
                    'Имя пользователя не соответствует регулярному выражению'
                )
            )
        ]
    )
    email = models.EmailField(
        'Электронная почта пользователя',
        max_length=128,
        unique=True
    )
    USERNAME_FIELD = 'email'
    first_name = models.CharField(
        'Имя пользователя',
        max_length=128,
    )
    last_name = models.CharField(
        'Фамилия пользователя',
        max_length=128,
    )
    avatar = models.ImageField(
        'Аватар пользователя',
        blank=False,
        upload_to='images/custom_users',
        null=True
    )

    REQUIRED_FIELDS = [
        'username',
        'last_name',
        'first_name'
    ]

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email


class Subscribe(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Подписчик автора рецепта'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='authors'
    )

    class Meta:
        verbose_name = 'Подписка'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscribe_user_author'
            ),
        ]
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} - подписчик автора: {self.author}'
