# New /start sequence

## General flow 
### Scenario 0 (already registered)
User enters `/start`, or uses deeplink with start.

Check in the DB table `bot_forum_registrations`. If there is an entry – pass to `main` dialog.


### Scenario 1 (from link)
User uses deeplink: e.g. `https://t.me/CBC_forum_bot?start=reg-190122`

Check for `reg-`. Extract 6-number code. 

Find matching code in `site_registrations` db table. Use matching data sequence (see Data matching)


### Scenario 2 (from bot)
User enters /start. Check in the DB table `bot_forum_registrations`. If no entry, start dialog `start_help`. 


## `Start_help` dialog
### 1. `want_reg`
```html
Привет!

Ты хочешь пройти или продолжить регистрацию на форум КБК 26? 
```
Buttons:
```text
"Да" (SwitchTo() - site_reg)
"Нет" (Start() - MainMenuSG.MAIN, ShowMode=RESET_STACK)
```
### 2. `site_reg`
```html
Проходил ли ты регистрацию на сайте?
```
Buttons:
```text
"Да" (SwitchTo() - id_enter)
"Нет" (SwitchTo() - need_reg)
```

### 3. `need_reg`
```html
Чтобы пользоваться ботом, необходимо пройти регистрацию на сайте.

Переходи по ссылке и заполни форму. Потом тебе выдадут ссылку на бота – возвращяйся по ней, чтобы закончить регистрацию! Или вводи полученный код. 

Контакты:
Общие вопросы: @cbc_assistant
Тех. поддержка: @zobko
```
Buttons:
```text
"Регистрация на сайте" (URL() - "https://forum-cbc.ru/registration.html")
"У уже меня есть код" (SwitchTo() - id_enter)
```

### 3. `need_reg`
```html
Введи свой уникальный код, полученный после регистрации на сайте.
```
Buttons:
```text
"Назад к регистрации" (SwitchTo() - need_reg)
```
TextInput() – see **Implementation details – Unique ID handling**

### 4. `wrong_code`
```html
Код неверный или мы не смогли найти его 😢

Попробуй еще раз ввести код или пройти регистрацию.


Если проблема сохраняется, мы всегда на связи!
Тех. поддержка: @zobko
```
Buttons:
```text
"Назад к регистрации" (SwitchTo() - need_reg)
```
TextInput() – see **Implementation details – Unique ID handling**


## Implemetation details

### DB 
Table `bot_forum_registrations`:
1. id – pk
2. user_id – fk to users
3. unique_id - fk to site_registration 
4. name
5. status – "speaker", "guest", "participant", "online_participant"
6. adult18
7. region
8. occupation_status
9. education
10. track
11. transport
12. car_number
13. passport

We need to separate from site_registrations becuase it is affected by separate application. We will user only `bot_forum_registrations`, so there is no need to create ORM for it. Use SQLAlchemy Core query builder. Do not forget to user standard means of accessing db through middleware. 


### Data matching
We match data from `site_registrations` and `bot_forum_registrations`. This is a crucial step to match telegram account to site registrations by bypassing human factor – no manual ID input. 

Users get a deeplink and uniqie code when registration is successful. 

We find that code upon recieving it in bot and find entry from site registration. Then poplate `bot_forum_registrations`. Also populate info to `user_info`:
1. full_name
2. email
3. username (if any)
4. education (if any)


### Unique ID handling
Make sure that one unique id can be used for only one telegram account. Therefore once an entry to `bot_forum_registrations` is created unique id is locked to an account. If someone else tries to use it, they will be denied as if it was not correct or does not exist. 