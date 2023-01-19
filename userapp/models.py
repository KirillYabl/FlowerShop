from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        florist = 'флорист'
        courier = 'курьер'

    @property
    def is_florist(self):
        return self.role == self.Role.florist

    @property
    def is_courier(self):
        return self.role == self.Role.courier

    role = models.CharField('роль', max_length=10, choices=Role.choices, null=True, blank=True)
