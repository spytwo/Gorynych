import random

from .models import Statictics, UserGame, Word

consonant_letters = ["Б", "В", "Г", "Д", "К", "Л", "М", "Н", "П", "Р", "С", "Т", "У"]
vowel_letters = ["А", "Е", "И", "О", "Я"]
rare_letters = ["Ф", "Х", "Ц", "Ч", "Ж", "З", "Ю"]
the_rarest = ["Й", "Щ", "Ь", "Ё", "Ы", "Э", "Ш"]
first_phrase = [
    "Круто!",
    "Фантастика!",
    "Невероятно!",
    "Классное слово!",
    "Полегче!",
    "Ничего себе вы придумали!",
    "Вы молодец!",
    "Отлично!",
]
second_phrase = [
    "Держите голову",
    "Награждаетесь головой",
    "Голова уже на месте",
    "Получаете голову",
    "Голова ваша",
    "Плюс голова",
    "Даю вам голову",
]
third_phrase = [
    "Но голову дать не могу.",
    "Но к сожалению, без добавления головы.",
    "Но без головы в этот раз.",
]
fourth_phrase = [
    "У Горыныча все головы на месте",
    "Голов у Горыныча полный комплект",
    "Горыныч в полном составе",
]


def get_rec():
    """Получает список рекордов из БД"""
    r = [(i.user, i.record, i.game_for_record) for i in UserGame.objects.all()]
    r.sort(key=lambda x: x[1], reverse=True)
    return r


def comp_words():
    """Возвращает множество, составленное из слов из БД"""
    res = {i.word for i in Word.objects.all()}
    return res


class Words:
    def __init__(self):
        self.deck = (
            random.sample(consonant_letters, 6)
            + random.sample(vowel_letters, 3)
            + random.sample(rare_letters, 1)
            + random.sample(the_rarest, 1)
        )
        self.number_user = 3
        self.number_comp = 3
        self.players_word_list = []
        self.comp_word_list = set()
        self.final_comp_word_list = set()
        self.temp = 0
        self.gorynych_user = []
        self.gorynych_comp = []
        self.words_without_repeating_user = []
        self.words_without_repeating_comp = []

    def checking_for_all_letters(self, w: str):
        w = w.strip()
        """ Проверка слова игрока """
        if w in self.players_word_list:
            return "Такое слово уже есть"
        dict_of_letters = {}
        for i in w:
            if i not in self.deck:
                return f'Буквы "{i}" нет в колоде'
            elif i not in dict_of_letters:
                dict_of_letters[i] = 1
            else:
                dict_of_letters[i] += 1
        sum_letters = sum(dict_of_letters.values())  # Количество всех символов
        count_letters = len(dict_of_letters)  # Количество уникальных символов
        if self.number_user == 0 and sum_letters > count_letters:
            return "Горыныч без голов"
        if self.number_user < sum_letters - count_letters:
            return "Для этого слова не хватает голов у Горыныча"
        else:
            self.temp = (
                sum_letters - count_letters
            )  # Количество использованных голов Горыныча в данном слове
            self.number_user -= self.temp
            if self.temp != 0:
                self.gorynych_user.append(w)
        self.players_word_list.append(w)
        # Прибавление головы Горыныча за длинные слова без повторов
        if self.temp == 0:
            if len(w) > 5:
                # Когда три головы и добавляется длинное слово
                if self.number_user == 3:
                    self.temp += 1
                    self.words_without_repeating_user.append(w)
                    # Возвращается случайная фраза без прибавления головы
                    return f"{random.choice(first_phrase)} {random.choice(third_phrase)} {random.choice(fourth_phrase)}"
                elif self.number_user < 3:
                    self.number_user += 1
                self.words_without_repeating_user.append(w)
                # Возвращается случайная фраза с прибавлением головы
                return f"{random.choice(first_phrase)} {random.choice(second_phrase)}"
        if len(self.players_word_list) % 20 == 0 and self.number_user < 3:
            self.number_user += 1
            return "Вы вернули одну голову"

    def words_of_comp(self):
        """Первая проверка слова компьютера"""
        for word in comp_words():
            for letter in word.upper():
                if letter not in self.deck:
                    break
            else:
                self.comp_word_list.add(word.upper())

    def check_words_of_comp(self):
        """Вторая проверка слова компьютера"""
        for word in self.comp_word_list:
            dict_of_letters_comp = {}
            for letter in word:
                if letter not in dict_of_letters_comp:
                    dict_of_letters_comp[letter] = 1
                else:
                    dict_of_letters_comp[letter] += 1
            # Количество букв в слове
            sum_letters = sum(dict_of_letters_comp.values())
            # Количество уникальных букв в слове
            count_letters = len(dict_of_letters_comp)
            if self.number_comp == 0 and sum_letters > count_letters:
                continue
            if self.number_comp < sum_letters - count_letters:
                continue
            else:
                # Если у Горыныча компа есть головы
                self.number_comp -= sum_letters - count_letters
                # Если слово с повторами букв
                if sum_letters - count_letters != 0:
                    # Добавляем с список Горынычей компа
                    self.gorynych_comp.append(word)
                # Если слово длинее 5 букв и без повторов
                if sum_letters - count_letters == 0 and sum_letters > 5:
                    # Добавляем в список слов без повторов Горыныча
                    self.words_without_repeating_comp.append(word)
                    # Добавляем Горынычу компа одну голову
                    self.number_comp += 1
            self.final_comp_word_list.add(word)

    def who_won(self):
        """Определяет победителя"""
        if len(self.players_word_list) < len(self.final_comp_word_list):
            return "Вы проиграли", "проиграл(а)"
        if len(self.players_word_list) == len(self.final_comp_word_list):
            return "Ничья", "Ничья"
        return "Вы победили!", "победил(а)"

    def all_gorynych_comp(self):
        """Вовращает полный список слов-голов Горыныча"""
        set_final = self.final_comp_word_list
        set_first = self.comp_word_list
        all_word = set_first - set_final
        return list(all_word)

    def update_statistics(self, user):
        """Обновляет количество побед, ничьих, поражений"""
        stat = Statictics.objects.get(user_id=user)
        stat.number_of_games += 1
        if len(self.players_word_list) < len(self.final_comp_word_list):
            stat.defeat += 1
        if len(self.players_word_list) == len(self.final_comp_word_list):
            stat.dead_heat += 1
        if len(self.players_word_list) > len(self.final_comp_word_list):
            stat.victory += 1
        stat.save()
