from django.db import models


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=128
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=128
    )

    class Meta:
        verbose_name = 'Ингредиент'
        constraints = [
            models.UniqueConstraint(
                fields=['measurement_unit', 'name'],
                name='unique_myingredient_name_measurement-unit'
            )
        ]
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f"{self.name} - {self.measurement_unit}"
