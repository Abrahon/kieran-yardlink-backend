from django.db import models


class GrassTypeChoices(models.TextChoices):
    BERMUDA = "bermuda", "Bermuda"
    ZOYSIA = "zoysia", "Zoysia"
    FESCUE = "fescue", "Fescue"
    KENTUCKY_BLUEGRASS = "kentucky_bluegrass", "Kentucky Bluegrass"
    RYEGRASS = "ryegrass", "Ryegrass"
    ST_AUGUSTINE = "st_augustine", "St. Augustine"
    CENTIPEDE = "centipede", "Centipede"
