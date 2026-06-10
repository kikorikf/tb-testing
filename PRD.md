# PRD — ТБ-Допуск: система ежедневного тестирования по технике безопасности

**Версия:** 1.1  
**Дата:** 2026-06-10  
**Статус:** Draft  
**Изменения v1.1:** добавлен раздел управления вопросами (FR-ENG-06 – FR-ENG-10), рандомизация порядка вопросов и вариантов ответов, API CRUD `/questions`, обновлена схема БД таблицы `questions`.

---

## 1. Контекст и цель

Инсталляторы ежедневно получают наряды-допуска на производство работ через систему WFM. В текущем процессе (AS-IS) допуск выдаётся вручную инженером после проведения планёрки по ТБ — без фиксации результата и без цифрового подтверждения. Это создаёт риски: сложно отследить, прошёл ли конкретный сотрудник инструктаж, и нет документального следа апрува.

**Цель TO-BE:** создать мини-приложение, которое каждый день в 00:00 автоматически блокирует наряды ВФМ для всех инсталляторов, обязывает каждого пройти тест по ТБ, и разблокирует доступ только после успешного прохождения теста и явного апрува инженера. Результат фиксируется в виде JSON наряда-допуска и хранится отдельно в профилях обоих участников.

---

## 2. Роли пользователей

| Роль | Описание |
|---|---|
| **Инсталлятор** | Проходит тест по ТБ каждый день. Получает доступ к нарядам ВФМ только после апрува инженера. Видит свои JSON наряды-допуска в профиле. |
| **Инженер** | Получает уведомление о результате теста инсталлятора. Апрувит или отклоняет допуск. Управляет банком вопросов (создание, редактирование, удаление, активация). Видит свои JSON наряды-допуска в профиле. |
| **Система** | Выполняет ежедневный сброс (00:00): блокирует ВФМ, обнуляет статус допуска. Генерирует и сохраняет JSON наряда при апруве. |

Идентификация ролей — через Keycloak Realm Roles (`installer`, `engineer`).

---

## 3. Бизнес-процесс (TO-BE)

```
00:00 каждый день
  └─ Система блокирует ВФМ для всех инсталляторов
  └─ Инсталлятор открывает приложение → видит экран "Пройдите тест по ТБ"
  └─ Нажимает "Начать тест" → запускается таймер 30 мин, 5+ вопросов
       ├─ Не прошёл (< 70%) или вышло время → уведомление, повтор
       └─ Прошёл (≥ 70%) → отправляется уведомление инженеру (ФИО, результат, время)
            └─ Инженер получает карточку в очереди апрувов
                 ├─ Отклонил → инсталлятор видит статус "отклонено", повтор теста
                 └─ Апрувил → система генерирует JSON наряда-допуска
                                └─ JSON сохраняется в профиле инсталлятора И в профиле инженера
                                └─ ВФМ разблокируется для инсталлятора на текущий день
                                └─ Инсталлятор получает доступ к нарядам ВФМ
```

---

## 4. Функциональные требования

### 4.1 Инсталлятор

**FR-INS-01** — при входе в приложение система проверяет статус допуска на текущий день. Если допуск не получен — отображается экран блокировки с кнопкой "Начать тест". Наряды ВФМ недоступны.

**FR-INS-02** — после нажатия "Начать тест" запускается сессия теста: таймер 30 минут, вопросы отображаются по одному, доступны кнопки "Назад" / "Далее" / "Сдать тест". Порядок вопросов и порядок вариантов ответов внутри каждого вопроса случайный для каждой сессии (Fisher-Yates shuffle на бэкенде).

**FR-INS-03** — при истечении таймера тест автоматически завершается с результатом 0%, сессия закрывается, отображается кнопка повтора.

**FR-INS-04** — порог прохождения — 70% правильных ответов. Количество попыток не ограничено.

**FR-INS-05** — после успешной сдачи инсталлятор видит свой результат (%, количество верных, время) и статус "Ожидание апрува инженера". Повторная сдача до получения результата апрува недоступна.

**FR-INS-06** — после апрува инженера инсталлятор видит статус "Доступ открыт", кнопки перехода к нарядам ВФМ и к JSON наряда-допуска.

**FR-INS-07** — таб "Наряды ВФМ" заблокирован (с поясняющим сообщением) до получения апрува. После апрува — загружает наряды через `GET /api/wfm-shift-be/v1.0/shift`.

**FR-INS-08** — в профиле инсталлятора хранится отдельный список JSON нарядов-допуска (по одному на каждый день прохождения). Данные персистируются в БД, не теряются при обновлении страницы.

### 4.2 Инженер

**FR-ENG-01** — инженер видит очередь апрувов: список инсталляторов, прошедших тест. Каждая карточка содержит ФИО, результат в %, количество верных ответов, затраченное время.

**FR-ENG-02** — инженер нажимает "Подтвердить" или "Отклонить". Оба действия необратимы в рамках текущей сессии.

**FR-ENG-03** — при апруве система генерирует JSON наряда-допуска и сохраняет его в профиле инженера (в отдельном списке) и в профиле инсталлятора. После этого ВФМ разблокируется для инсталлятора.

**FR-ENG-04** — таб "История" показывает все апрувы и отклонения инженера за текущий день.

**FR-ENG-05** — в профиле инженера хранится отдельный список JSON нарядов-допуска, которые он апрувил. Структура JSON идентична инсталляторскому хранилищу.

**FR-ENG-06** — инженер имеет доступ к разделу "Банк вопросов" (отдельный таб). Отображается таблица всех вопросов с колонками: текст вопроса, количество вариантов, статус (активен / неактивен), дата создания, дата последнего изменения.

**FR-ENG-07** — инженер может создать новый вопрос: ввести текст вопроса, добавить от 2 до 6 вариантов ответа, отметить один правильный вариант, установить статус (активен / неактивен). Вопрос сохраняется в БД.

**FR-ENG-08** — инженер может редактировать любое поле существующего вопроса: текст, варианты ответов, правильный вариант, статус. Изменения применяются только к будущим сессиям — уже запущенные сессии используют снапшот вопросов на момент старта.

**FR-ENG-09** — инженер может деактивировать вопрос (мягкое удаление: `is_active = false`). Деактивированный вопрос не попадает в тест, но сохраняется в БД и остаётся видимым в таблице с отметкой "Неактивен". Полного удаления нет — только деактивация.

**FR-ENG-10** — система выдаёт предупреждение если количество активных вопросов меньше минимально необходимого для формирования теста (< 5). Сохранение деактивации при этом возможно, но инженер видит предупреждение.

### 4.3 Система / фоновые задачи

**FR-SYS-01** — ежедневно в 00:00 (cron) система сбрасывает статус допуска для всех инсталляторов (`daily_access.status = 'locked'`).

**FR-SYS-02** — при апруве инженера система POST-ит в WFM наряд через `POST /api/wfm-shift-be/v1.0/shift` и сохраняет JSON в БД.

**FR-SYS-03** — уведомление инженеру о новом результате теста — через polling (каждые 10 сек) или WebSocket (предпочтительно).

---

## 5. Нефункциональные требования

| Требование | Значение |
|---|---|
| Протокол | HTTPS обязательно |
| Аутентификация | Keycloak (OpenID Connect, JWT Bearer) |
| Доступность | не менее 99% в рабочие часы |
| Время ответа API | < 300 мс для всех эндпоинтов кроме генерации JSON |
| Браузеры | Chrome 110+, Edge 110+, Firefox 115+ |
| Мобильная адаптация | не требуется в v1 |

---

## 6. Стек технологий

| Слой | Технология |
|---|---|
| Frontend | React 18, TypeScript, Vite |
| Backend | Python 3.11+, FastAPI |
| БД | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.0 + Alembic (миграции) |
| Авторизация | Keycloak, `python-jose` для валидации JWT |
| Фоновые задачи | APScheduler (cron внутри FastAPI) или Celery + Redis |
| Внешний API | WFM Shift BE `https://10.6.4.118:6021/api/wfm-shift-be/v1.0` |
| Деплой | Docker Compose |

---

## 7. Схема базы данных (PostgreSQL)

### `users`
```sql
CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  keycloak_id   VARCHAR(255) UNIQUE NOT NULL,  -- sub из JWT
  employee_id   INTEGER UNIQUE,                -- ID в системе WFM
  full_name     VARCHAR(255) NOT NULL,
  role          VARCHAR(50) NOT NULL CHECK (role IN ('installer', 'engineer')),
  created_at    TIMESTAMPTZ DEFAULT now()
);
```

### `questions`
```sql
CREATE TABLE questions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  text          TEXT NOT NULL,
  options       JSONB NOT NULL,   -- массив строк: ["вариант А", "вариант Б", ...]
  correct       INTEGER NOT NULL, -- индекс правильного ответа в оригинальном массиве options
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  created_by    UUID REFERENCES users(id),
  updated_by    UUID REFERENCES users(id),
  created_at    TIMESTAMPTZ DEFAULT now(),
  updated_at    TIMESTAMPTZ DEFAULT now()
);

-- автообновление updated_at
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER questions_updated_at
  BEFORE UPDATE ON questions
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

> **Рандомизация.** Перемешивание порядка вопросов и вариантов ответов выполняется **на бэкенде** при вызове `POST /test/start`. Фронтенд получает уже перемешанный список. В `test_sessions.answers` ответы хранятся по `question_id` с индексом варианта **в оригинальном** (`options`) массиве, чтобы проверка результата не зависела от порядка показа.

### `test_sessions`
```sql
CREATE TABLE test_sessions (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  installer_id UUID NOT NULL REFERENCES users(id),
  session_date DATE NOT NULL DEFAULT CURRENT_DATE,
  started_at   TIMESTAMPTZ NOT NULL,
  submitted_at TIMESTAMPTZ,
  status       VARCHAR(30) NOT NULL
               CHECK (status IN ('in_progress', 'passed', 'failed', 'timed_out')),
  score_pct    INTEGER,
  correct_cnt  INTEGER,
  total_cnt    INTEGER,
  duration_sec INTEGER,
  answers      JSONB         -- {question_id: selected_index, ...}
);
CREATE INDEX ON test_sessions (installer_id, session_date);
```

### `daily_access`
```sql
CREATE TABLE daily_access (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  installer_id UUID NOT NULL REFERENCES users(id),
  access_date  DATE NOT NULL DEFAULT CURRENT_DATE,
  status       VARCHAR(30) NOT NULL
               CHECK (status IN ('locked', 'pending_approval', 'approved', 'rejected')),
  session_id   UUID REFERENCES test_sessions(id),
  engineer_id  UUID REFERENCES users(id),
  decided_at   TIMESTAMPTZ,
  UNIQUE (installer_id, access_date)
);
```

### `permits`
```sql
CREATE TABLE permits (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  permit_id     VARCHAR(100) UNIQUE NOT NULL,  -- НД-20260610-АД
  installer_id  UUID NOT NULL REFERENCES users(id),
  engineer_id   UUID NOT NULL REFERENCES users(id),
  session_id    UUID NOT NULL REFERENCES test_sessions(id),
  permit_date   DATE NOT NULL,
  valid_until   TIMESTAMPTZ NOT NULL,
  generated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  payload       JSONB NOT NULL    -- полный JSON наряда-допуска
);
CREATE INDEX ON permits (installer_id, permit_date);
CREATE INDEX ON permits (engineer_id,  permit_date);
```

---

## 8. Backend API (FastAPI)

Base URL: `/api/v1`  
Все эндпоинты требуют заголовка `Authorization: Bearer {keycloak_token}`.

---

### 8.1 Auth / профиль

#### `GET /me`
Возвращает профиль текущего пользователя из БД (создаёт запись при первом входе).

**Response 200:**
```json
{
  "id": "uuid",
  "keycloak_id": "...",
  "employee_id": 132,
  "full_name": "Дюсенов Алмас Бекович",
  "role": "installer"
}
```

---

### 8.2 Тестирование

#### `GET /test/status`
Статус допуска инсталлятора на текущий день.

**Response 200:**
```json
{
  "date": "2026-06-10",
  "status": "locked",
  "session_id": null,
  "score_pct": null,
  "permit_id": null
}
```
`status` ∈ `locked | in_progress | pending_approval | approved | rejected`

---

#### `POST /test/start`
Создаёт новую тест-сессию. Выбирает все активные вопросы, перемешивает их порядок (Fisher-Yates), внутри каждого вопроса перемешивает варианты ответов, сохраняет маппинг `shuffled_index → original_index` в `test_sessions` для корректной проверки. Возвращает вопросы без индикации правильного ответа.

**Response 201:**
```json
{
  "session_id": "uuid",
  "started_at": "2026-06-10T08:00:00Z",
  "expires_at": "2026-06-10T08:30:00Z",
  "questions": [
    {
      "id": "uuid",
      "text": "Что необходимо сделать перед началом работы...",
      "options": ["Позвонить мастеру", "Надеть СИЗ...", "Подождать 10 минут", "Сразу приступить..."]
    }
  ]
}
```
> Порядок `options` в ответе отличается от порядка в БД — варианты перемешаны. Клиент отображает их как есть и отправляет индекс выбранного варианта **в перемешанном** массиве. Бэкенд при `submit` переводит обратно в оригинальный индекс для проверки.

**Ошибки:** `409` — активная сессия уже есть или допуск уже получен; `403` — роль не `installer`; `422` — активных вопросов меньше минимума (5).

---

#### `POST /test/submit`
Принимает ответы, вычисляет результат, обновляет `test_sessions` и `daily_access`.

**Request:**
```json
{
  "session_id": "uuid",
  "answers": {
    "question-uuid-1": 0,
    "question-uuid-2": 2
  }
}
```

**Response 200:**
```json
{
  "session_id": "uuid",
  "status": "passed",
  "score_pct": 80,
  "correct_cnt": 4,
  "total_cnt": 5,
  "duration_sec": 272,
  "passed": true
}
```

**Ошибки:** `404` — сессия не найдена; `410` — истёк таймер; `409` — сессия уже завершена.

---

### 8.3 Апрув (инженер)

#### `GET /approvals/pending`
Список инсталляторов, ожидающих апрув на сегодня.

**Response 200:**
```json
[
  {
    "daily_access_id": "uuid",
    "installer": {
      "id": "uuid",
      "employee_id": 132,
      "full_name": "Дюсенов Алмас Бекович"
    },
    "session": {
      "id": "uuid",
      "score_pct": 80,
      "correct_cnt": 4,
      "total_cnt": 5,
      "duration_sec": 272,
      "submitted_at": "2026-06-10T08:04:32Z"
    }
  }
]
```

---

#### `POST /approvals/{daily_access_id}/approve`
Апрувит допуск, генерирует JSON наряда, вызывает POST в WFM.

**Response 200:**
```json
{
  "permit_id": "НД-20260610-АД",
  "generated_at": "2026-06-10T08:15:00Z",
  "wfm_synced": true
}
```

**Ошибки:** `404` — не найден; `409` — уже решён; `403` — роль не `engineer`.

---

#### `POST /approvals/{daily_access_id}/reject`
Отклоняет допуск. Инсталлятор сможет пройти тест повторно.

**Request:**
```json
{ "reason": "Недостаточный результат" }
```

**Response 200:**
```json
{ "daily_access_id": "uuid", "status": "rejected" }
```

---

#### `GET /approvals/history`
История апрувов инженера за текущий день.

**Response 200:**
```json
[
  {
    "daily_access_id": "uuid",
    "installer_full_name": "Дюсенов Алмас Бекович",
    "status": "approved",
    "score_pct": 80,
    "decided_at": "2026-06-10T08:15:00Z",
    "permit_id": "НД-20260610-АД"
  }
]
```

---

### 8.4 Наряды допуска

#### `GET /permits/my`
Список всех JSON нарядов-допуска текущего пользователя (для обеих ролей).

**Query params:** `date_from`, `date_to` (опционально, `YYYY-MM-DD`).

**Response 200:**
```json
[
  {
    "permit_id": "НД-20260610-АД",
    "permit_date": "2026-06-10",
    "valid_until": "2026-06-10T23:59:59Z",
    "generated_at": "2026-06-10T08:15:00Z",
    "installer": {
      "employee_id": 132,
      "full_name": "Дюсенов Алмас Бекович",
      "role": "installer"
    },
    "engineer": {
      "full_name": "Кенжебеков Нуртай",
      "role": "engineer"
    },
    "test_result": {
      "score_pct": 80,
      "correct_answers": 4,
      "total_questions": 5,
      "duration": "4м 32с"
    },
    "wfm_access": {
      "unlocked": true,
      "shift_date": "2026-06-10",
      "employee_id": 132
    }
  }
]
```

---

#### `GET /permits/my/{permit_id}`
Один наряд по ID. `404` если не найден или не принадлежит пользователю.

---

### 8.5 Управление вопросами (инженер)

Все эндпоинты доступны только с ролью `engineer`.

---

#### `GET /questions`
Список всех вопросов (активных и неактивных).

**Query params:** `is_active` (bool, опционально — фильтр по статусу).

**Response 200:**
```json
[
  {
    "id": "uuid",
    "text": "Что необходимо сделать перед началом работы с электроустановкой?",
    "options": ["Надеть СИЗ и проверить инструмент", "Сразу приступить", "Позвонить мастеру", "Подождать 10 минут"],
    "correct": 0,
    "is_active": true,
    "created_by": "uuid",
    "updated_by": "uuid",
    "created_at": "2026-06-01T10:00:00Z",
    "updated_at": "2026-06-10T08:00:00Z"
  }
]
```

---

#### `POST /questions`
Создать новый вопрос.

**Request:**
```json
{
  "text": "Текст вопроса",
  "options": ["Вариант А", "Вариант Б", "Вариант В", "Вариант Г"],
  "correct": 1,
  "is_active": true
}
```

**Валидация:**
- `text` — непустая строка, не длиннее 1000 символов
- `options` — массив от 2 до 6 непустых строк
- `correct` — целое число, валидный индекс в массиве `options`

**Response 201:**
```json
{
  "id": "uuid",
  "text": "Текст вопроса",
  "options": ["Вариант А", "Вариант Б", "Вариант В", "Вариант Г"],
  "correct": 1,
  "is_active": true,
  "created_at": "2026-06-10T09:00:00Z"
}
```

**Ошибки:** `422` — нарушение валидации.

---

#### `GET /questions/{question_id}`
Один вопрос по ID.

**Response 200:** объект из `GET /questions`.  
**Response 404:** не найден.

---

#### `PATCH /questions/{question_id}`
Частичное обновление вопроса. Изменения применяются только к **будущим** тест-сессиям.

**Request (все поля опциональны):**
```json
{
  "text": "Обновлённый текст вопроса",
  "options": ["Новый А", "Новый Б", "Новый В"],
  "correct": 0,
  "is_active": true
}
```

> Если передаются `options` без `correct` или наоборот — бэкенд валидирует что `correct` остаётся валидным индексом для нового массива `options`.

**Response 200:** обновлённый объект вопроса.

**Ошибки:** `404` — не найден; `422` — `correct` выходит за пределы нового массива `options`; `409` — попытка деактивировать последний активный вопрос, если активных вопросов останется меньше 5 (возвращает предупреждение, но **не блокирует** сохранение — клиент показывает предупреждение).

---

#### `DELETE /questions/{question_id}`
Мягкое удаление: устанавливает `is_active = false`. Физического удаления нет.

**Response 200:**
```json
{
  "id": "uuid",
  "is_active": false,
  "active_questions_remaining": 4,
  "warning": "Активных вопросов меньше минимума (5). Тест временно недоступен."
}
```

**Ошибки:** `404` — не найден.

---

### 8.6 Наряды ВФМ (прокси)

#### `GET /wfm/shifts`
Прокси к внешнему WFM API. Доступен только при `daily_access.status = 'approved'` на сегодня.

**Query params:** `shift_date` (опционально, по умолчанию сегодня).

Бэкенд вызывает:
```
GET https://10.6.4.118:6021/api/wfm-shift-be/v1.0/shift
    ?employeeId={employee_id}&shiftDate={shift_date}
```

**Response 200:**
```json
[
  {
    "shiftId": "НД-20260610-01",
    "location": "Цех №3, линия А",
    "type": "day",
    "startTime": "2026-06-10T08:00:00.000Z",
    "endTime":   "2026-06-10T17:00:00.000Z"
  }
]
```

**Ошибки:** `403` — допуск не получен.

---

#### `POST /wfm/shifts` (вызывается внутренне при апруве)
Бэкенд вызывает при апруве инженера:
```
POST https://10.6.4.118:6021/api/wfm-shift-be/v1.0/shift
```
```json
{
  "employeeId": 132,
  "startTime": "2026-06-10T08:00:00.000Z",
  "endTime":   "2026-06-10T17:00:00.000Z"
}
```

> Бэкенд использует сервисный аккаунт Keycloak (`client_credentials` flow) для авторизации в WFM, не прокидывая пользовательский токен напрямую.

---

### 8.7 Фоновая задача — ежедневный сброс

Cron: `0 0 * * *` (00:00 каждый день).

Логика:
1. Для всех пользователей с `role = 'installer'` вставить запись в `daily_access` с `status = 'locked'` на текущую дату (если записи ещё нет).
2. Логировать количество созданных записей.

Реализация: APScheduler внутри FastAPI процесса.

---

## 9. Авторизация (Keycloak)

```
Client (frontend):  tb-testing-app       — public, PKCE
Client (backend):   tb-testing-backend   — confidential, client_credentials
```

| Realm Role | Доступ |
|---|---|
| `installer` | тест, наряды ВФМ (после апрува), свои наряды-допуска |
| `engineer`  | очередь апрувов, история, управление вопросами (`/questions/*`), свои наряды-допуска |

JWT claims для инсталлятора (настроить Attribute mapper в KC):
```json
{
  "sub": "keycloak-uuid",
  "name": "Дюсенов Алмас Бекович",
  "employee_id": 132,
  "realm_access": { "roles": ["installer"] }
}
```

---

## 10. Структура проекта

```
tb-testing/
├── frontend/                   # React 18 + TypeScript + Vite
│   ├── src/
│   │   ├── api/                # axios-инстанс, типы запросов/ответов
│   │   ├── components/         # переиспользуемые компоненты
│   │   ├── pages/
│   │   │   ├── installer/      # TestScreen, WFMScreen, Profile
│   │   │   └── engineer/
│   │   │       ├── ApprovalQueue.tsx
│   │   │       ├── History.tsx
│   │   │       ├── Profile.tsx
│   │   │       └── questions/
│   │   │           ├── QuestionBank.tsx   # таблица вопросов
│   │   │           ├── QuestionForm.tsx   # форма создания/редактирования
│   │   │           └── QuestionRow.tsx    # строка с инлайн-деактивацией
│   │   ├── hooks/              # useTestSession, useApprovals, usePermits, useQuestions
│   │   ├── store/              # Zustand
│   │   └── keycloak.ts
│   └── vite.config.ts
│
├── backend/                    # Python 3.11 + FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py       # env vars (pydantic-settings)
│   │   │   ├── security.py     # валидация JWT (python-jose)
│   │   │   └── scheduler.py    # APScheduler cron
│   │   ├── db/
│   │   │   ├── session.py      # AsyncSession
│   │   │   └── models.py       # SQLAlchemy 2.0 models
│   │   ├── routers/
│   │   │   ├── me.py
│   │   │   ├── test.py
│   │   │   ├── approvals.py
│   │   │   ├── permits.py
│   │   │   ├── questions.py    # CRUD вопросов
│   │   │   └── wfm.py
│   │   ├── schemas/            # Pydantic v2
│   │   ├── services/
│   │   │   ├── test_service.py       # shuffle + проверка ответов
│   │   │   ├── question_service.py   # CRUD + валидация минимума
│   │   │   ├── permit_service.py
│   │   │   └── wfm_client.py         # httpx-клиент к WFM API
│   │   └── migrations/         # Alembic
│   ├── pyproject.toml
│   └── Dockerfile
│
├── docs/
│   └── tb_testing_to_be.bpmn
├── docker-compose.yml
├── PRD.md
└── README.md
```

---

## 11. Docker Compose

```yaml
version: "3.9"
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: tb_testing
      POSTGRES_USER: tb_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://tb_user:${DB_PASSWORD}@db:5432/tb_testing
      KEYCLOAK_URL: ${KEYCLOAK_URL}
      KEYCLOAK_REALM: ${KEYCLOAK_REALM}
      WFM_BASE_URL: https://10.6.4.118:6021/api/wfm-shift-be/v1.0
      WFM_CLIENT_ID: ${WFM_CLIENT_ID}
      WFM_CLIENT_SECRET: ${WFM_CLIENT_SECRET}
    depends_on: [db]
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    environment:
      VITE_API_URL: https://${BACKEND_HOST}/api/v1
      VITE_KEYCLOAK_URL: ${KEYCLOAK_URL}
      VITE_KEYCLOAK_REALM: ${KEYCLOAK_REALM}
      VITE_KEYCLOAK_CLIENT_ID: tb-testing-app
    ports:
      - "3000:80"

volumes:
  pg_data:
```

---

## 12. Этапы разработки

### Этап 1 — Backend core (1 неделя)
- Настройка FastAPI, PostgreSQL, Alembic
- Миграции: `users`, `questions`, `test_sessions`, `daily_access`, `permits`
- Seed: начальный набор вопросов (≥ 10) через Alembic data migration
- Эндпоинты: `/me`, `/test/start` (с shuffle), `/test/submit`, `/test/status`
- Валидация JWT через Keycloak JWKS
- Cron сброс в 00:00

### Этап 2 — Апрув, вопросы, интеграция WFM (1 неделя)
- Эндпоинты: `/approvals/*`, `/permits/my`, `/wfm/shifts`
- CRUD `/questions/*` с валидацией минимума активных вопросов
- httpx-клиент к WFM (сервисный KC токен)
- Генерация и сохранение JSON наряда-допуска

### Этап 3 — Frontend React (1.5 недели)
- Инициализация Keycloak, роут-гарды по роли
- Экраны инсталлятора: тест (таймер, вопросы в случайном порядке, прогресс-бар), статус ожидания, ВФМ, профиль с нарядами
- Экраны инженера: очередь апрувов, история, профиль с нарядами
- Раздел "Банк вопросов": таблица, форма создания/редактирования, деактивация с предупреждением
- Polling (`GET /approvals/pending` каждые 10с) или WebSocket для уведомлений

### Этап 4 — Интеграция и тестирование (0.5 недели)
- E2E-тест полного флоу: старт → тест → апрув → ВФМ
- Тест флоу управления вопросами: создание → редактирование → деактивация → проверка что вопрос пропал из теста
- Проверка HTTPS (WFM с внутренним CA)
- Деплой Docker Compose

---

## 13. Открытые вопросы

| # | Вопрос | Ответственный |
|---|---|---|
| 1 | Нужна ли ротация из пула (выдавать N случайных из всех активных, а не все сразу)? | Product |
| 2 | Cooldown между попытками (сейчас — мгновенный повтор)? | Product |
| 3 | Нужно ли уведомление инженеру через push/email, или только in-app polling? | Product |
| 4 | Сертификат для `10.6.4.118` — внутренний CA или самоподписанный? | DevOps |
| 5 | `shiftDate` в WFM GET — формат `YYYYMMDD` или `YYYY-MM-DD`? | WFM team |
| 6 | Нужен ли архив нарядов за прошлые дни или только текущий? | Product |
| 7 | Можно ли инженеру физически удалять вопросы (сейчас только деактивация)? | Product |
| 8 | Нужна ли история изменений вопросов (кто, когда, что изменил)? | Product |
