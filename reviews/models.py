from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User


class LandscaperReview(models.Model):
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="given_reviews"
    )
    landscaper = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_reviews"
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("client", "landscaper")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.client.email} → {self.landscaper.email} ({self.rating})"
