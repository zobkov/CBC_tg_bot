-- Вставка заявок из CSV файла
-- Файл: 011_insert_csv_applications.sql

-- Сначала добавляем пользователей в таблицу users (если их там еще нет)
INSERT INTO users (user_id, language, is_alive, is_blocked, submission_status)
VALUES 
  -- Получаем user_id из Telegram username, здесь используем временные ID
  -- В реальности нужно будет заменить на реальные Telegram user_id
  (1001, 'ru', true, false, 'submitted'), -- @bugassha
  (1002, 'ru', true, false, 'not_submitted') -- @hlorsson
ON CONFLICT (user_id) DO NOTHING;

-- Теперь добавляем заявки в таблицу applications
INSERT INTO applications (
    user_id,
    full_name,
    university,
    phone,
    email,
    telegram_username,
    how_found_kbk,
    previous_department,
    department_1,
    subdepartment_1,
    position_1,
    department_2,
    subdepartment_2,
    position_2,
    department_3,
    subdepartment_3,
    position_3,
    experience,
    motivation,
    created,
    updated
) VALUES 
  (
    865431031, -- user_id для @bugassha
    'Бугаева Ксения Денисовна',
    'ВШМ СПбГУ, 1 курс',
    '89029927576',
    'st143890@student.spbu.ru',
    '@bugassha',
    NULL, -- Как нашли - пусто в CSV
    NULL, -- Предыдущий отдел - пусто в CSV
    'Отдел SMM&PR',
    'Социальные сети на русском и китайском',
    'Контент-менеджер',
    'Отдел SMM&PR',
    'Социальные сети на русском и китайском',
    'Рилсмейкер',
    'Отдел логистики и ИТ',
    NULL, -- Под-отдел 3 пустой
    'Логист',
    'Касаемо моего опыта в проектах, связанных с логистикой, к сожалению, я не участвовала (
Однако есть опыт в создании эстетичных видео, а также рилс. Более того, я сама веду личную страничку в инстаграмме, стараюсь создавать красивый визуал, порой пишу посты, а также выкладываю красивые (по мнению многих моих друзей и знакомых) сторис
С детства увлекаюсь редактированием видео. Очень люблю творить по-настоящему красивый контент! Была бы безумно рада принять участие в данном проекте КБК
Из опыта в съемке рилсов, я снимала и монтировала рилсы для подружек, а также немного помогала с контентом в школе.
По поводу отдела логистики, я достаточно осторожна, аккуратна и при этом не медлительна, за счет чего считаю, что справилась бы в критической ситуации.
Если вдруг захочется взглянуть на мой профиль и работы в инстаграмме, посмотреть визуал, то оставлю свой ник) @bugassha',
    'Я очень хочу быть в команде КБК по нескольким причинам:
Возможность проявить себя
Наработать скилл в создании рилсов и визуала, для меня это очень важно, так как сама интересуюсь этой сферой. Кстати говоря, я достаточно самокритичный человек в отношении фотографий и редактировании, так что все всегда довожу до идеала. Если мне скажут переделать-я без проблем доведу работу до самой настоящей «конфетки»
Довольно-таки необычный проект, но мне очень нравится, что он
международный, хочу набраться опыта именно в такой среде.
 Интересно повзаимодействовать с ребятами, которые давно в сфере контент-креаторства, а также с теми, кто только начинает. И я ОЧЕНЬ хочу получить советы от ребят, кто уже прям на опыте, я думаю это поможет мне смотреть на контент-вещи по типу составления визуала и рилсов с другой стороны, а это крайне важно для прогресса и буста навыков в той или иной сфере🙏🏻',
    NOW(),
    NOW()
  ),
  (
    1611830001, -- user_id для @hlorsson
    'Мельнов Тимур Александрович',
    'СпБГУПТД, ИГД (Институт графического дизайна), 4 курс, выпуск 2028',
    '79627365678',
    'hlorsson@gmail.com',
    '@hlorsson',
    NULL, -- Как нашли - пусто в CSV
    NULL, -- Предыдущий отдел - пусто в CSV
    'Отдел дизайна',
    NULL, -- Под-отдел 1 пустой
    'Иллюстратор',
    NULL, -- Отдел 2 пустой
    NULL, -- Под-отдел 2 пустой
    NULL, -- Позиция 2 пустая
    NULL, -- Отдел 3 пустой
    NULL, -- Под-отдел 3 пустой
    NULL, -- Позиция 3 пустая
    NULL, -- Опыт пустой
    NULL, -- Мотивация пустая
    NOW(),
    NOW()
  )
ON CONFLICT (user_id) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    university = EXCLUDED.university,
    phone = EXCLUDED.phone,
    email = EXCLUDED.email,
    telegram_username = EXCLUDED.telegram_username,
    how_found_kbk = EXCLUDED.how_found_kbk,
    previous_department = EXCLUDED.previous_department,
    department_1 = EXCLUDED.department_1,
    subdepartment_1 = EXCLUDED.subdepartment_1,
    position_1 = EXCLUDED.position_1,
    department_2 = EXCLUDED.department_2,
    subdepartment_2 = EXCLUDED.subdepartment_2,
    position_2 = EXCLUDED.position_2,
    department_3 = EXCLUDED.department_3,
    subdepartment_3 = EXCLUDED.subdepartment_3,
    position_3 = EXCLUDED.position_3,
    experience = EXCLUDED.experience,
    motivation = EXCLUDED.motivation,
    updated = NOW();

-- Теперь добавляем записи в таблицу evaluated_applications
-- На основе колонок "Одобрен 1", "Одобрен 2", "Одобрен 3" из CSV
INSERT INTO evaluated_applications (
    user_id,
    accepted_1,
    accepted_2, 
    accepted_3,
    created,
    updated
) VALUES 
  (
    865431031, -- user_id для @bugassha
    true,  -- Одобрен 1: "Да"
    true,  -- Одобрен 2: "Да"  
    true,  -- Одобрен 3: "Да"
    NOW(),
    NOW()
  ),
  (
    1611830001, -- user_id для @hlorsson
    false, -- Одобрен 1: пусто (считаем как false)
    false, -- Одобрен 2: пусто (считаем как false)
    false, -- Одобрен 3: пусто (считаем как false)
    NOW(),
    NOW()
  )
ON CONFLICT (user_id) DO UPDATE SET
    accepted_1 = EXCLUDED.accepted_1,
    accepted_2 = EXCLUDED.accepted_2,
    accepted_3 = EXCLUDED.accepted_3,
    updated = NOW();

-- Обновляем submission_status в таблице users на основе статуса заявки
UPDATE users 
SET submission_status = (
    CASE 
        WHEN applications.status = 'submitted' THEN 'submitted'
        ELSE 'not_submitted'
    END
),
updated = NOW()
FROM applications 
WHERE users.user_id = applications.user_id;