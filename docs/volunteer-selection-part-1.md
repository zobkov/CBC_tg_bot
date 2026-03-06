# Volunteer selection

## General information 
Dialog path: `app/bot/dialogs/selections/creative`

### States
State: `VolunteerSelectionSG`
- MAIN
- name


## Dialog user flow

### MAIN
```html
<b>Привет!</b>

Мы очень рады, что ты проявил(а) желание стать волонтером и помогать нам в этом году. 
С помощью этого бота ты сможешь пройти первый этап отбора на волонтёрство.
```
Buttons:
- `Начать` – SwitchTo(MAIN)
- `Назад` - Cancel()

---

### General information

First we check for existing information in user_info table. 
If fields not NULL:
- full_name
- email
- education

Then show confirmation window: confirmation

If at least one NULL. Then SwitchTo(name)

#### confirmation
```html
<b>Мы нашли твои данные: </b>

ФИО: {full_name}
Почта: {email}
Образование: {education}

Они верны? 
```
Buttons: 
- `Да!` – SwitchTo(phone)
- `Нет. Надо заполнить заново` – SwitchTo(name)



#### name
```html
<b>Напиши, пожалуйста, свое ФИО</b>

Например: Иванов Иван Иванович
```
TextInput

#### email
```html
<b>Укажи свою почту</b>

Если ты из СПбГУ, то надо использовать корпоративную почту (должна заканчиваться на @spbu.ru, @student.spbu.ru или @gsom.spbu.ru)

Например: st118676@student.spbu.ru
```
TextInput

#### education
```html
<b>Напиши, где ты учишься</b>

Пиши в таком формате: СПбГУ, Юрфак, 3, 2027
```

---

**Compulsory input:**

### phone
```html
<b>Введи свой номер телефона</b>

Например: +79139736363 или 89216273306 
```
TextInput

### volunteer_dates
```html
<b>Когда ты можешь помогать?</b>

1. Только в сам день форума (11 апреля 2026)
2. В день форума и могу помочь в день до КБК (10 и 11 апреля 2026)
```
Buttons: 
- `1. Только 11 апреля` – "single" (how to write to db)
- `2. 10 и 11 апреля` - "double"

### function
```html
<b>Какой функционал ты хочешь выполнять на КБК?</b>

1. Общий волонтерский функционал
2. Фотографирование
3. Перевод
```
Buttons: 
- `1. Общий волонтерский функционал` – "general" – SwitchTo()
- `2. Фотографирование` - "photo" – SwitchTo()
- `3. Перевод` - "translate" – SwitchTo()



