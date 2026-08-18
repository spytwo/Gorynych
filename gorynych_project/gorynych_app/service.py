import random
from collections import Counter

from .models import Statictics, UserGame, Word

CONSONANT_LETTERS = [
    "Б",
    "В",
    "Г",
    "Д",
    "К",
    "Л",
    "М",
    "Н",
    "П",
    "Р",
    "С",
    "Т",
    "У",
]

VOWEL_LETTERS = ["А", "Е", "И", "О", "Я"]

RARE_LETTERS = ["Ф", "Х", "Ц", "Ч", "Ж", "З", "Ю"]

THE_RAREST_LETTERS = ["Й", "Щ", "Ь", "Ё", "Ы", "Э", "Ш"]

FIRST_PHRASES = [
    "Круто!",
    "Фантастика!",
    "Невероятно!",
    "Классное слово!",
    "Полегче!",
    "Ничего себе вы придумали!",
    "Вы молодец!",
    "Отлично!",
]

SECOND_PHRASES = [
    "Держите голову",
    "Награждаетесь головой",
    "Голова уже на месте",
    "Получаете голову",
    "Голова ваша",
    "Плюс голова",
    "Даю вам голову",
]

THIRD_PHRASES = [
    "Но голову дать не могу.",
    "Но к сожалению, без добавления головы.",
    "Но без головы в этот раз.",
]

FOURTH_PHRASES = [
    "У Горыныча все головы на месте",
    "Голов у Горыныча полный комплект",
    "Горыныч в полном составе",
]

MAX_HEADS = 3
WORDS_FOR_HEAD = 20
LONG_WORD_LENGTH = 5


def get_rec():
    """Возвращает список рекордов пользователей."""
    records = [
        (game.user, game.record, game.game_for_record)
        for game in UserGame.objects.all()
    ]
    return sorted(records, key=lambda record: record[1], reverse=True)


def comp_words():
    """Возвращает множество слов из БД."""
    return {word.word for word in Word.objects.all()}


class Words:
    def __init__(self):
        self.deck = self._create_deck()
        self.number_user = MAX_HEADS
        self.number_comp = MAX_HEADS
        self.players_word_list = []
        self.comp_word_list = set()
        self.final_comp_word_list = set()
        self.temp = 0
        self.gorynych_user = []
        self.gorynych_comp = []
        self.words_without_repeating_user = []
        self.words_without_repeating_comp = []

    @staticmethod
    def _create_deck():
        return (
            random.sample(CONSONANT_LETTERS, 6)
            + random.sample(VOWEL_LETTERS, 3)
            + random.sample(RARE_LETTERS, 1)
            + random.sample(THE_RAREST_LETTERS, 1)
        )

    def checking_for_all_letters(self, word: str):
        """Проверяет слово игрока и изменяет состояние игры."""
        word = word.strip()

        if word in self.players_word_list:
            return "Такое слово уже есть"

        letter_counts = Counter(word)

        missing_letter = next(
            (letter for letter in word if letter not in self.deck),
            None,
        )
        if missing_letter:
            return f'Буквы "{missing_letter}" нет в колоде'

        repeated_letters = sum(letter_counts.values()) - len(letter_counts)

        error = self._check_heads(repeated_letters)
        if error:
            return error

        self._add_player_word(word, repeated_letters)

        return self._get_word_reward(word)

    def _check_heads(self, repeated_letters):
        """Проверяет, хватает ли голов Горыныча для слова."""
        if self.number_user == 0 and repeated_letters > 0:
            return "Горыныч без голов"

        if self.number_user < repeated_letters:
            return "Для этого слова не хватает голов у Горыныча"

        return None

    def _add_player_word(self, word, repeated_letters):
        """Добавляет слово игрока и списывает использованные головы."""
        self.temp = repeated_letters
        self.number_user -= repeated_letters
        self.players_word_list.append(word)

        if repeated_letters:
            self.gorynych_user.append(word)

    def _get_word_reward(self, word):
        """Обрабатывает награду за длинное слово без повторяющихся букв."""
        if self.temp != 0:
            return None

        if len(word) > LONG_WORD_LENGTH:
            self.words_without_repeating_user.append(word)

            if self.number_user == MAX_HEADS:
                self.temp = 1
                return self._no_head_reward()

            self.number_user += 1
            return self._head_reward()

        if len(self.players_word_list) % WORDS_FOR_HEAD == 0:
            if self.number_user < MAX_HEADS:
                self.number_user += 1
                return "Вы вернули одну голову"

        return None

    @staticmethod
    def _head_reward():
        return f"{random.choice(FIRST_PHRASES)} {random.choice(SECOND_PHRASES)}"

    @staticmethod
    def _no_head_reward():
        return (
            f"{random.choice(FIRST_PHRASES)} "
            f"{random.choice(THIRD_PHRASES)} "
            f"{random.choice(FOURTH_PHRASES)}"
        )

    def words_of_comp(self):
        """Первая проверка слов компьютера."""
        for word in comp_words():
            word = word.upper()

            if all(letter in self.deck for letter in word):
                self.comp_word_list.add(word)

    def check_words_of_comp(self):
        """Вторая проверка слов компьютера."""
        for word in self.comp_word_list:
            repeated_letters = self._count_repeated_letters(word)

            if not self._can_comp_use_word(repeated_letters):
                continue

            self._use_comp_heads(word, repeated_letters)
            self.final_comp_word_list.add(word)

    @staticmethod
    def _count_repeated_letters(word):
        letter_counts = Counter(word)
        return len(word) - len(letter_counts)

    def _can_comp_use_word(self, repeated_letters):
        if self.number_comp == 0 and repeated_letters > 0:
            return False

        return self.number_comp >= repeated_letters

    def _use_comp_heads(self, word, repeated_letters):
        self.number_comp -= repeated_letters

        if repeated_letters:
            self.gorynych_comp.append(word)
            return

        if len(word) > LONG_WORD_LENGTH:
            self.words_without_repeating_comp.append(word)
            self.number_comp += 1

    def who_won(self):
        """Определяет победителя."""
        player_words = len(self.players_word_list)
        computer_words = len(self.final_comp_word_list)

        if player_words < computer_words:
            return "Вы проиграли", "проиграл(а)"

        if player_words == computer_words:
            return "Ничья", "Ничья"

        return "Вы победили!", "победил(а)"

    def all_gorynych_comp(self):
        """Возвращает слова, которые могли бы использовать головы Горыныча."""
        return list(self.comp_word_list - self.final_comp_word_list)

    def update_statistics(self, user):
        """Обновляет статистику пользователя."""
        stat = Statictics.objects.get(user_id=user)

        player_words = len(self.players_word_list)
        computer_words = len(self.final_comp_word_list)

        stat.number_of_games += 1

        if player_words < computer_words:
            stat.defeat += 1
        elif player_words == computer_words:
            stat.dead_heat += 1
        else:
            stat.victory += 1

        stat.save()
