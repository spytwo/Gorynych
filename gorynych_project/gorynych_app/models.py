from django.contrib.auth.models import User
from django.db import models


class Word(models.Model):
    word = models.CharField(max_length=99, verbose_name="Слова", unique=True)
    objects = models.Manager()

    def __str__(self):
        return self.word

    class Meta:
        verbose_name = "Слово"
        verbose_name_plural = "Слова"


class UserGame(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    game = models.BinaryField(null=True)
    record = models.IntegerField(default=0)
    game_for_record = models.BinaryField(null=True)
    objects = models.Manager()

    def __str__(self):
        return f"{self.user}"

    class Meta:
        verbose_name = "Игра игрока"
        verbose_name_plural = "Игры игроков"


class Statictics(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    number_of_games = models.IntegerField(verbose_name="Количество игр", default=0)
    victory = models.IntegerField(verbose_name="Победы", default=0)
    dead_heat = models.IntegerField(verbose_name="Ничьи", default=0)
    defeat = models.IntegerField(verbose_name="Поражения", default=0)
    objects = models.Manager()

    def __str__(self):
        return f"{self.user}"

    class Meta:
        verbose_name = "Статистика"
        verbose_name_plural = "Статистика"


class Record(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    record_1 = models.IntegerField(verbose_name="Рекорд", default=0)
    record_2 = models.IntegerField(verbose_name="Рекорд", default=0)
    record_3 = models.IntegerField(verbose_name="Рекорд", default=0)
    objects = models.Manager()

    def __str__(self):
        return f"{self.user}"

    class Meta:
        verbose_name = "Рекорд"
        verbose_name_plural = "Рекорды"
