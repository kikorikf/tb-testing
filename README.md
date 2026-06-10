# ТБ-Допуск — приложение тестирования по технике безопасности

## Структура проекта

```
tb-testing/
├── src/
│   └── index.html        # всё приложение (single-page, без зависимостей)
├── docs/
│   └── tb_testing_to_be.bpmn   # BPMN TO-BE процесс
└── README.md
```

---

## Роли

| Роль | Что видит |
|---|---|
| **Инсталлятор** | Тест по ТБ, статус апрува, наряды ВФМ (только после апрува), профиль с JSON нарядов |
| **Инженер** | Очередь апрувов с ФИО/результатом/временем, история, профиль с JSON нарядов |

---

## WFM API (уже вшито)

```
Base URL: https://10.6.4.118:6021/api/wfm-shift-be/v1.0
```

### GET смены инсталлятора
```
GET /shift?employeeId={id}&shiftDate={YYYYMMDD}
Headers: Authorization: Bearer {token}
```

### POST наряд
```
POST /shift
Headers: Authorization: Bearer {token}
Body:
{
  "employeeId": 132,
  "startTime": "2026-06-10T08:00:00.000Z",
  "endTime":   "2026-06-10T17:00:00.000Z"
}
```

> ⚠️ Сертификат на `10.6.4.118` — самоподписанный или внутренний CA.
> В браузере нужно один раз открыть `https://10.6.4.118:6021` и принять исключение,
> либо добавить корневой CA в доверенные.

---

## Подключение Keycloak

### 1. Добавить скрипт KC в `<head>` (перед закрывающим тегом)

```html
<script src="https://<KEYCLOAK_HOST>/auth/js/keycloak.js"></script>
```

### 2. Инициализировать KC в конце `<script>` вместо текущего `INIT`

```js
const keycloak = new Keycloak({
  url:      'https://<KEYCLOAK_HOST>/auth',
  realm:    '<REALM>',
  clientId: 'tb-testing-app'
});

keycloak.init({ onLoad: 'login-required' }).then(authenticated => {
  if (!authenticated) { keycloak.login(); return; }

  // Передать токен в CFG
  CFG.AUTH_TOKEN = keycloak.token;

  // Обновлять токен каждые 30 сек
  setInterval(() => {
    keycloak.updateToken(30).then(refreshed => {
      if (refreshed) CFG.AUTH_TOKEN = keycloak.token;
    });
  }, 30000);

  // Определить роль и показать нужный экран
  const roles = keycloak.realmAccess?.roles || [];
  const isEngineer  = roles.includes('engineer');
  const isInstaller = roles.includes('installer');

  // Скрыть DEMO-переключатель
  document.getElementById('demo-switch').style.display = 'none';

  // Подставить имя из KC-токена
  const name = keycloak.idTokenParsed?.name || keycloak.idTokenParsed?.preferred_username || '';
  const initials = name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0,2);
  document.getElementById('topbar-name').textContent = name;
  document.getElementById('topbar-av').textContent = initials;

  if (isEngineer) {
    switchRole('engineer');
  } else {
    switchRole('installer');
    // Подставить employeeId из KC claims (если настроен mapper)
    if (keycloak.idTokenParsed?.employee_id) {
      CFG.INSTALLER_EMPLOYEE_ID = keycloak.idTokenParsed.employee_id;
    }
  }
});
```

### 3. Роли в Keycloak (Realm Roles)

| Роль KC | Что открывает |
|---|---|
| `installer` | экран инсталлятора |
| `engineer`  | экран инженера |

### 4. Logout

```js
// добавить кнопку в topbar:
keycloak.logout({ redirectUri: window.location.origin });
```

---

## Структура JSON наряда допуска

Генерируется при апруве инженера, хранится отдельно в профиле инсталлятора и в профиле инженера.

```json
{
  "permit_id": "НД-20260610-АД",
  "date": "2026-06-10",
  "valid_until": "2026-06-10T23:59:59Z",
  "generated_at": "2026-06-10T09:15:00.000Z",
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
```

---

## TODO (следующие шаги)

- [ ] Подключить Keycloak (см. выше)
- [ ] Вынести вопросы теста в `questions.json` + загружать через `fetch()`
- [ ] Персистить наряды допуска в backend (сейчас только in-memory)
- [ ] WebSocket или polling для нотификации инженера в реальном времени
- [ ] Добавить HTTPS-сертификат для `10.6.4.118` в доверенные / настроить nginx proxy
- [ ] Ограничить повторную сдачу теста (cooldown между попытками)
