# Volunteer selection

## General information 
Dialog path: `app/bot/dialogs/selections/creative`

### States
State: `VolunteerSelectionSG`
- MAIN
- confirmation
- name
- email
- education
- phone
- volunteer_dates
- function
- general_1
- general_1_1
- general_1_2
- general_1_3
- general_2
- general_3
- additional_information_prompt
- photo_1
- photo_2
- photo_3
- photo_4
- translate_1
- translate_2
- translate_2_certificate
- translate_3
- translate_3_1
- translate_3_2
- translate_4
- additional_information_prompt
- END

## Implementation details

1. Create DB infrastructre:
   1. New table: volunteer_selection
   2. Field are corresponding to all answers.
   3. Add or update info in user_info: name, email, education, phone
2. Create google sheets syncronization like in creative_selection
   1. Table: https://docs.google.com/spreadsheets/d/1jxr_eYgEVEvXRq175fFNdQIrLG_z9XQ_nSjTFZZSBss/edit?gid=0#gid=0
   2. Credentials are the same
   3. List name: Applications
   4. Add scheduler for every hour batch update. 
   5. Hook this syncronization into /sync_google. Replace creative selection there. 
3. Ensure proper DB session usage. It is passed thorugh middleware. Commits and rollbacks are handled there as well. 
4. Entry point – MainMenu
   1. Button: `💁 Отбор Волонтеров` 

---

# Dialog user flow

## MAIN
### If not applied:
```html
<b>Привет!</b>

Мы очень рады, что ты проявил(а) желание стать волонтером и помогать нам в этом году. 
С помощью этого бота ты сможешь пройти первый этап отбора на волонтёрство.
```
Buttons:
- `Начать` – SwitchTo(MAIN)
- `Назад` - Cancel()

### Text if applied:
```html
✅ <b>Заявка уже отправлена!</b>

Мы вернемся с результатами первого этапа отбора <b>16 марта</b>. 

Хочешь что-то уточнить? Не стесняйся и пиши нам, мы на связи: @savitsanastya @drkirna
```
Buttons:
- `Начать` – SwitchTo(MAIN)
- `Назад` - Cancel()

---

## General information

First we check for existing information in user_info table. 
If fields not NULL:
- full_name
- email
- education

Then show confirmation window: confirmation

If at least one NULL. Then SwitchTo(name)

### confirmation
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



### name
```html
<b>Напиши, пожалуйста, свое ФИО</b>

Например: Иванов Иван Иванович
```
TextInput

### email
```html
<b>Укажи свою почту</b>

Если ты из СПбГУ, то надо использовать корпоративную почту (должна заканчиваться на @spbu.ru, @student.spbu.ru или @gsom.spbu.ru)

Например: st118676@student.spbu.ru
```
TextInput

### education
```html
<b>Напиши, где ты учишься</b>

Пиши в таком формате: СПбГУ, Юрфак, 3, 2027
```

---

## Compulsory input:

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
- `1. Общий волонтерский функционал` – "general" – SwitchTo(general_1)
- `2. Фотографирование` - "photo" – SwitchTo()
- `3. Перевод` - "translate" – SwitchTo()


## General branch

### general_1
```html
<b>Посещал(а) ли ты когда-то КБК в качестве участника или волонтера?</b>
```
Buttons: 
- `1. Да, в качестве участника` – "guest" – SwitchTo(general_1_1)
- `2. Да, в качестве волонтера` - "volunteer" – SwitchTo(general_1_2)
- `3. Да, как волонтер и как участник` - "guest_and_volunteer" – SwitchTo(general_1_3)
- `4. Нет` - "no" – SwitchTo(general_2)

#### general_1_1
```html
<b>Поделись своим опытом участия.</b>

Что тебе понравилось, а что, по твоему мнению, можно улучшить? 
<i>(обязательно ответь на обе части вопроса)</i>
```
TextInput – switchTo(general_2)

#### general_1_2
```html
<b>Поделись своим опытом волонтерства.</b>

Что тебе понравилось, а что, по твоему мнению, можно улучшить? 
<i>(обязательно ответь на обе части вопроса)</i>
```
TextInput – switchTo(general_2)

#### general_1_3
```html
<b>Поделись своим опытом участия/волонтерства.</b>

Что тебе понравилось, а что, по твоему мнению, можно улучшить? 
<i>(обязательно ответь на обе части вопроса)</i>
```
TextInput – switchTo(general_2)

!!!
***Note: write general_1_1, general_1_2 or general_1_3 to the same field: general_1_answer***


### general_2
```html
<b>Почему именно КБК?</b> 

Почему тебе хочется стать волонтером на этом мероприятии?
```
TextInput – switchTo(general_3)

### general_3
```html
<b>Как ты считаешь, какие твои личностные качества будут наиболее полезны для работы в команде волонтёров КБК?</b>

Приведи примеры из своего опыта/жизни, когда твои качества помогали тебе решить проблему.
```
TextInput – switchTo(additional_information_prompt)


## Photo branch

### photo_1
```html
<b>Прикрепи ссылку на свое портфолио.</b>

(облачное хранилище, сайт, Instagram с работами)
```
TextInput – switchTo(photo_2)

### photo_2
```html
<b>Есть ли у тебя свое оборудование?</b>
```
Buttons: 
- `Да` – "yes" – SwitchTo(photo_3)
- `Нет` - "no" – SwitchTo(photo_3)

### photo_3
```html
<b>Есть ли у тебя опыт фото/видеосъемки на мероприятиях?</b>

Расскажи, на каких.
```
TextInput – switchTo(photo_4)

### photo_4
```html
<b>Как ты думаешь, какие ключевые моменты и эмоции важно запечатлеть фотографу на КБК, чтобы передать атмосферу форума?</b>
```
TextInput – switchTo(additional_information_prompt)


## Translation branch

### translate_1
```html
<b>Какой у тебя уровень китайского?</b>
```
TextInput – switchTo(translate_2)



### translate_2
```html
<b>Есть ли у тебя подтверждающий сертификат (HSK и др.)?</b>
```
Buttons: 
- `Да` – "yes" – SwitchTo(translate_2_certificate)
- `Нет` - "no" – SwitchTo(translate_3)

### translate_2_certificate
```html
<b>Прикрепи ссылку на свой сертификат, пожалуйста.</b>

На облачное хранилище: Google Drive, Яндекс.Диск и т.п.
```
TextInput – switchTo()



### translate_3
```html
<b>Был ли у тебя опыт общения на китайском языке?</b>
```
Buttons: 
- `Да` – "yes" – SwitchTo(translate_3_1)
- `Нет` - "no" – SwitchTo(translate_4)


### translate_3_1
```html
<b>Расскажи подробнее, какой у тебя был опыт общения на китайском языке?</b>

(учеба, работа, путешествия)
```
TextInput – switchTo(translate_3_2)

### translate_3_2
```html
<b>Работал(а) ли ты когда-то с иностранными спикерами/гостями?</b>

Поделись своим опытом.
```
TextInput – switchTo(translate_4)



### translate_4
```html
<b>Представь ситуацию: во время перевода ты не понял(а) или усомнился(ась) в точности сказанного говорящим.</b>

Как бы ты поступил(а)?
```
TextInput – switchTo(additional_information_prompt)

## Ending

### additional_information_prompt
```html
<b>Есть ли что-то, что мы не спросили, но что важно, чтобы мы о тебе знали? Или у тебя есть вопросы к нам?</b>
```
TextInput – switchTo(additional_information_prompt)


### END
```html
<b>Спасибо за твои ответы!</b> Мы вернемся с результатами первого этапа отбора <b>16 марта</b>. 

Хочешь что-то уточнить? Не стесняйся и пиши нам, мы на связи: @savitsanastya @drkirna
```
Buttons: 
- `В главное меню` – Cancel()
