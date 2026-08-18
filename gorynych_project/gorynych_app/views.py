import pickle

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render

from .forms import UserLoginForm, UserRegForm
from .models import Record, Statictics, UserGame
from .service import Words, get_rec


def index(request):
    """Главная страница игры."""
    try:
        games = UserGame.objects.get(user=request.user)
    except ObjectDoesNotExist:
        return redirect("login")

    game = pickle.loads(games.game)

    if request.method != "POST":
        return _render_game(request, game)

    handlers = {
        "add": _add_word,
        "cancel": _cancel_word,
        "count": _count_words,
        "check": _finish_game,
        "end": _new_game,
        "doc": _show_rules,
        "logout": _logout,
        "rec": _show_records,
    }

    for action, handler in handlers.items():
        if action in request.POST:
            return handler(request, games, game)

    return _render_game(request, game)


def _render_game(request, game, **context):
    """Рендерит главную страницу игры."""
    context = {"game": game, **context}
    return render(request, "gorynych_app/index.html", context=context)


def _save_game(games, game):
    """Сохраняет состояние игры."""
    games.game = pickle.dumps(game)
    games.save()


def _add_word(request, games, game):
    """Добавляет слово игрока."""
    word = request.POST.get("word", "").upper()
    result = game.checking_for_all_letters(word)

    _save_game(games, game)

    return _render_game(request, game, res=result)


def _cancel_word(request, games, game):
    """Удаляет последнее слово игрока."""
    if game.players_word_list:
        _restore_heads_after_cancel(game)
        _remove_last_word(game)

    _save_game(games, game)

    return _render_game(request, game)


def _restore_heads_after_cancel(game):
    """Возвращает головы Горыныча после удаления слова."""
    if len(game.players_word_list) % 20 == 0:
        game.number_user += game.temp
        game.players_word_list.pop()

        if game.number_user > 0:
            game.number_user -= 1

        game.temp = 0
        return

    last_word = game.players_word_list[-1]

    if (
        len(last_word) > 5
        and len(last_word) == len(set(last_word))
        and (game.number_user == 3 and game.temp == 1 or game.number_user > 0)
    ):
        game.number_user -= 1

    game.number_user += game.temp


def _remove_last_word(game):
    """Удаляет последнее слово из всех соответствующих списков."""
    word = game.players_word_list.pop()

    if word in game.gorynych_user:
        game.gorynych_user.remove(word)

    if word in game.words_without_repeating_user:
        game.words_without_repeating_user.remove(word)

    game.temp = 0


def _count_words(request, games, game):
    """Показывает количество слов игрока."""
    result = f"Количество ваших слов: {len(game.players_word_list)}"
    return _render_game(request, game, res=result)


def _finish_game(request, games, game):
    """Заканчивает текущую игру и показывает результат."""
    game.words_of_comp()
    game.check_words_of_comp()
    _add_remaining_comp_heads(game)

    game.update_statistics(request.user.id)
    _update_records(games, game)

    result_game = game
    _save_record_if_needed(games, game)

    games.game = pickle.dumps(Words())
    games.save()

    return render(
        request,
        "gorynych_app/final.html",
        context={"game_2": result_game},
    )


def _add_remaining_comp_heads(game):
    """Добавляет компьютеру головы за оставшиеся подходящие слова."""
    heads_to_add = len(game.final_comp_word_list) // 20

    while heads_to_add > 0:
        available_words = game.all_gorynych_comp()

        if not available_words:
            break

        word = available_words.pop()
        game.gorynych_comp.append(word)
        game.final_comp_word_list.add(word)
        heads_to_add -= 1


def _update_records(games, game):
    """Обновляет три лучших результата пользователя."""
    record = Record.objects.get(user=games.user)

    records = [
        record.record_1,
        record.record_2,
        record.record_3,
    ]

    records.append(len(game.players_word_list))
    records.sort(reverse=True)

    record.record_1 = records[0]
    record.record_2 = records[1]
    record.record_3 = records[2]
    record.save()


def _save_record_if_needed(games, game):
    """Сохраняет игру, если установлен новый абсолютный рекорд."""
    score = len(game.players_word_list)

    if score <= games.record:
        return

    games.record = score
    games.game_for_record = pickle.dumps(game)
    games.save()


def _new_game(request, games, game):
    """Начинает новую игру."""
    games.game = pickle.dumps(Words())
    games.save()

    return redirect("index")


def _show_rules(request, games, game):
    """Показывает правила игры."""
    return render(
        request,
        "gorynych_app/rules.html",
        context={"game": game},
    )


def _logout(request, games, game):
    """Выход пользователя из аккаунта."""
    user_logout(request)
    return redirect("login")


def _show_records(request, games, game):
    """Показывает таблицу рекордов."""
    context = {
        "get_rec": get_rec,
        "user": games.user,
        "game": game,
    }

    return render(
        request,
        "gorynych_app/rec.html",
        context=context,
    )


def register(request):
    """Регистрация пользователя."""
    if request.method == "POST":
        form = UserRegForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            _create_user_game_data(user)

            messages.success(request, "Успешная регистрация")
            return redirect("index")

        messages.error(request, "Что-то пошло не так")
    else:
        form = UserRegForm()

    return render(
        request,
        "gorynych_app/register.html",
        context={"form": form},
    )


def _create_user_game_data(user):
    """Создаёт игровые данные нового пользователя."""
    UserGame.objects.create(
        game=pickle.dumps(Words()),
        user=user,
    )

    Statictics.objects.create(user=user)
    Record.objects.create(user=user)


def user_login(request):
    """Авторизация пользователя."""
    if request.method == "POST":
        form = UserLoginForm(data=request.POST)

        if form.is_valid():
            login(request, form.get_user())
            return redirect("index")
    else:
        form = UserLoginForm()

    return render(
        request,
        "gorynych_app/login.html",
        context={"form": form},
    )


def user_logout(request):
    """Выход пользователя."""
    logout(request)


def get_record_html(request, user):
    """Показывает сохранённую игру из рейтинга."""
    games = UserGame.objects.get(user__username=user)
    game = pickle.loads(games.game_for_record)

    return render(
        request,
        "gorynych_app/game_detail.html",
        context={
            "game": game,
            "user": games.user,
        },
    )


def statistics(request, user):
    """Показывает статистику пользователя."""
    user = User.objects.get(username=user)
    stat = Statictics.objects.filter(user=user)

    records = Record.objects.get(user=user)
    top_records = sorted(
        [
            records.record_1,
            records.record_2,
            records.record_3,
        ],
        reverse=True,
    )

    return render(
        request,
        "gorynych_app/statistics.html",
        context={
            "stat": stat,
            "user": user,
            "list_rec": top_records,
        },
    )
