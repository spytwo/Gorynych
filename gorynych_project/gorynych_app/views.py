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
    try:
        # Получаем запись по id игрока
        games = UserGame.objects.get(user_id=User.objects.get(username=request.user).id)
        # Десериализуем состояние игры игрока из БД
        game = pickle.loads(games.game)
    except ObjectDoesNotExist:
        # Если игрок не авторизован, то отправляется на страницу авторизации
        return redirect("login")
    context = {"game": game}
    if request.method == "POST" and "add" in request.POST:
        # При нажатии ДОБАВИТЬ
        word = request.POST.get("word").upper()
        res = game.checking_for_all_letters(word)
        new_context = {"res": res} | context
        # обновляем состояние игры в БД
        games.game = pickle.dumps(game)
        games.save()
        return render(request, "gorynych_app/index.html", context=new_context)
    if request.method == "POST" and "cancel" in request.POST:
        # При нажатии УБРАТЬ
        # Убрать голову Горыныча если удалил 20-е слово, за которое ее дали
        if len(game.players_word_list) % 20 == 0:
            game.number_user += game.temp
            game.players_word_list.pop()
            if game.number_user > 0:
                game.number_user -= 1
            game.temp = 0
        elif len(game.players_word_list) >= 1:
            if len(game.players_word_list[-1]) > 5 and len(
                game.players_word_list[-1]
            ) == len(set(game.players_word_list[-1])):
                # Когда уже было три головы и последнее слово длинное, которое нужно удалить
                if game.number_user == 3 and game.temp == 1 or game.number_user > 0:
                    game.number_user -= 1
            game.number_user += game.temp  # Возврат Горыныча при отмене слова
            w = game.players_word_list.pop()
            # Чтобы при удалении слова из общего списка, оно удалялось и из списка слов Горыныча, если оно там было
            if w in game.gorynych_user:
                game.gorynych_user.remove(w)
            # Чтобы при удалении слова из общего списка, оно удалялось и из списка уникальных слов
            # Горыныча, если оно там было
            if w in game.words_without_repeating_user:
                game.words_without_repeating_user.remove(w)
            game.temp = 0
        # обновляем состояние игры в БД
        games.game = pickle.dumps(game)
        games.save()
    if request.method == "POST" and "count" in request.POST:
        # При нажатии ПОСЧИТАТЬ
        res = f"Количество ваших слов: {len(game.players_word_list)}"
        new_context = {"res": res} | context
        return render(request, "gorynych_app/index.html", context=new_context)
    if request.method == "POST" and "check" in request.POST:
        # При нажатии ЗАКОНЧИТЬ ИГРУ
        game.words_of_comp()
        game.check_words_of_comp()
        count_new_words_for_comp = len(game.final_comp_word_list) // 20
        while len(game.all_gorynych_comp()) > 0 and count_new_words_for_comp > 0:
            new_word = game.all_gorynych_comp().pop()
            game.gorynych_comp.append(new_word)
            game.final_comp_word_list.add(new_word)
            count_new_words_for_comp -= 1
        game.update_statistics(request.user.id)

        # Обновляем топ-3 рекордов
        rec = Record.objects.get(user_id=request.user.id)
        list_rec = [rec.record_1, rec.record_2, rec.record_3]
        list_rec.sort(reverse=True)
        rec.record_1 = list_rec[0]
        rec.record_2 = list_rec[1]
        rec.record_3 = list_rec[2]
        rec.save()
        if len(game.players_word_list) > list_rec[2]:
            rec.record_3 = len(game.players_word_list)
            rec.save()

        # Делаем копию состояния игры для фронта
        game_2 = game
        new_context = {"game_2": game_2}
        # Если самый большой рекорд, то сохраняем
        if len(game.players_word_list) > games.record:
            # Сохраняем число рекорд
            games.record = len(game.players_word_list)
            games.save()
            # Сериализуем и сохраняем детальное состояние игры в БД
            games.game_for_record = pickle.dumps(game)
            games.save()
        # Создаем новую игру
        games.game = pickle.dumps(Words())
        games.save()
        # games.game = pickle.dumps(game)
        # games.save()
        return render(request, "gorynych_app/final.html", context=new_context)
    if request.method == "POST" and "end" in request.POST:
        # При нажатии НОВАЯ ИГРА
        # Создаем новую игру
        games.game = pickle.dumps(Words())
        games.save()
        return redirect("index")
    if request.method == "POST" and "doc" in request.POST:
        # При нажатии ПРАВИЛА
        return render(request, "gorynych_app/rules.html", context=context)
    if request.method == "POST" and "logout" in request.POST:
        # При нажатии ВЫЙТИ ИЗ АККАУНТА
        user_logout(request)
        return redirect("login")
    if request.method == "POST" and "rec" in request.POST:
        # При нажатии РЕКОРДЫ
        new_context = {"get_rec": get_rec, "user": games.user} | context
        return render(request, "gorynych_app/rec.html", context=new_context)
    return render(request, "gorynych_app/index.html", context=context)


def register(request):
    if request.method == "POST":
        form = UserRegForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Успешная регистрация")
            UserGame.objects.create(
                game=pickle.dumps(Words()), user_id=User.objects.get(username=user).id
            )
            Statictics.objects.create(user_id=User.objects.get(username=user).id)
            Record.objects.create(user_id=User.objects.get(username=user).id)
            return redirect("index")
        else:
            messages.error(request, "Что-то пошло не так")
    else:
        form = UserRegForm()
    context = {"form": form}
    return render(request, "gorynych_app/register.html", context=context)


def user_login(request):
    if request.method == "POST":
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("index")
    else:
        form = UserLoginForm()
    context = {"form": form}
    return render(request, "gorynych_app/login.html", context=context)


def user_logout(request):
    logout(request)
    return redirect("login")


def get_record_html(request, user):
    """Получение деталей игры игрока в рейтинге"""
    games = UserGame.objects.get(user_id=User.objects.get(username=user).id)
    game = pickle.loads(games.game_for_record)
    context = {"game": game, "user": games.user}
    return render(request, "gorynych_app/game_detail.html", context=context)


def statistics(request, user):
    user = User.objects.get(username=user)
    stat = Statictics.objects.filter(user=user)
    rec = Record.objects.get(user_id=user.id)
    list_rec = [rec.record_1, rec.record_2, rec.record_3]
    list_rec.sort(reverse=True)
    context = {"stat": stat, "user": user, "list_rec": list_rec}
    return render(request, "gorynych_app/statistics.html", context=context)
