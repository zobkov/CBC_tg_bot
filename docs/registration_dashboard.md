# Registration dashboard

## Idea
Create a service that pulls registration statics from tables: `site_registrations` and `bot_forum_registrations`; creates comprehensive statistics and generates reports of certain formats.


## Data and statistics needed
Use all data from these tables. 
Statistics:
- Number of registrations on site (`site_registrations`)
- Number of registration in bot (`bot_forum_registrations`)
- Number of registrations per track per both tables separately. 
- Number of registrations per status (speaker, participant, guest)


## Standard report format
```html
Отчет по регистрациям

Кол-во регистрация на сайте:
Кол-во регитсрации в боте: 
Конверсия: {x}%

Регистрации по трекам:
1. Финансы и инвестиции (Finance & Banking) — {n of bot_forum_registrations} / {n of site_registrations}
2. Логистика и ВЭД (Supply Chain & Trade) — {n of bot_forum_registrations} / {n of site_registrations}
3. Консалтинг и риск-менеджмент (Strategy & Consulting) — {n of bot_forum_registrations} / {n of site_registrations}
4. Политика, право и дипломатия (Rules of the Game) — {n of bot_forum_registrations} / {n of site_registrations}
5. Маркетинг и медиа (Digital & Brand) — {n of bot_forum_registrations} / {n of site_registrations}
6. Язык, культура и перевод (Humanities & Arts) — {n of bot_forum_registrations} / {n of site_registrations}
7. Китайский трек (Chinese Track) — {n of bot_forum_registrations} / {n of site_registrations}
8. Росмолодёжь.Гранты — {n of bot_forum_registrations} / {n of site_registrations}
```

## Output sources
### 1. /dashboard bot cmd
### 2. Send daily to chat
Set chat to: -5223773417
At time 10:00 moscow time zone
