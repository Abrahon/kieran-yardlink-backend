
# class ServiceCategory(models.TextChoices):
#     LAWN = "lawn", "Lawn"
#     GARDEN = "garden", "Garden"
#     TREE = "tree", "Tree"
#     IRRIGATION = "irrigation", "Irrigation"
#     CLEANUP = "cleanup", "Seasonal Cleanup"

from django.db import models

class ServiceCategory(models.TextChoices):
    LANDSCAPING = "landscaping", "Landscaping"
    LAWN_CARE = "lawn_care", "Lawn Care"
    TREE_TRIMMING = "tree_trimming", "Tree Trimming"
    IRRIGATION = "irrigation", "Irrigation"
    GARDEN_DESIGN = "garden_design", "Garden Design"
    PAVING = "paving", "Paving"
    FENCE_INSTALLATION = "fence_installation", "Fence Installation"
    OTHER = "other", "Other"
