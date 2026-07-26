from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


phone_validator = RegexValidator(
    regex=r'^\+?\d{7,15}$',
    message="Phone number must contain 7 to 15 digits and may start with '+'.",
)


class Contact(models.Model):
    """
    A single contact record, owned by the authenticated user who created it.
    Each user manages their own address book; contacts are never shared
    across users.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contacts',
    )
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, validators=[phone_validator])
    address = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=150, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            # Prevent the same user from storing the same email twice
            models.UniqueConstraint(
                fields=['owner', 'email'],
                name='unique_email_per_owner',
            ),
            # Prevent the same user from storing the same phone number twice
            models.UniqueConstraint(
                fields=['owner', 'phone_number'],
                name='unique_phone_per_owner',
            ),
        ]
        indexes = [
            models.Index(fields=['owner', 'name']),
            models.Index(fields=['owner', 'email']),
            models.Index(fields=['owner', 'phone_number']),
        ]

    def __str__(self):
        return f"{self.name} ({self.email})"
