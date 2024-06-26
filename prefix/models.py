from django.db import models
from django.contrib.auth.models import Group, User
from django.utils import timezone

class Prefix(models.Model):
    """
    """

    prefix = models.CharField(primary_key=True, max_length=5)
    certifying_key = models.TextField(blank=True, null=True)
    created = models.DateTimeField(
        default=timezone.now,
        blank=True,
        null=True
    )
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        to_field="username"
    )
    counter = models.IntegerField(
        default=0,
        help_text="Counter for object_id asignment"
    )
    public = models.BooleanField(
        default=True,
        help_text= "Boolean field to indicate if there are restrictions on "\
            + "the use of this prefix"
        )

    def __str__(self):
        """String for representing the BCO model (in Admin site etc.)."""
        return f"{self.prefix}"