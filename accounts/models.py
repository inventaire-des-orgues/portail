import uuid
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom user in which email must be unique
    """
    email = models.EmailField(
        _('email address'),
        null=True,
        blank=True,
        unique=True
    )

    uuid = models.UUIDField(
        db_index=True,
        default=uuid.uuid4,
        unique=True,
        editable=False
    )


    class Meta:
        ordering = ["last_name"]


    def get_full_name(self):
        """
        Returns the user full name or a representation of its identity.
        """
        if self.first_name or self.last_name:
            if self.first_name and self.last_name:
                return '{} {}'.format(self.first_name, self.last_name)
            else:
                return '{}{}'.format(self.first_name, self.last_name)
        elif self.email:
            return self.email
        else:
            return self.username

    def __str__(self):
        """
        Override default representation of an User object
        """
        return self.get_full_name()
