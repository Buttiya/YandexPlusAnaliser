# DataLens setup

Текущий рабочий API:

```text
http://ai360.velkerr.ru:40186
```

## Что создать в DataLens

1. Создай API Connector.
2. Заполни поля подключения именно так:

- Hostname: `ai360.velkerr.ru`
- Port: `40186`
- HTTPS: выключено
- URL path: пусто
- Allowed methods: `POST`

Не вставляй `http://ai360.velkerr.ru:40186` целиком в поле hostname.
Если DataLens показывает одно поле Base URL вместо отдельных полей, тогда укажи:

```text
http://ai360.velkerr.ru:40186
```

3. Скопируй ID API Connector.
4. Создай Editor chart / Advanced chart.
5. Открой файл `datalens-editor-current-server.js`.
6. Замени:

```js
YOUR_API_CONNECTION_ID
```

на ID API Connector.

7. Вставь файлы из папки `datalens-tabs` по вкладкам:

- `Meta` -> `datalens-tabs/Meta.json`
- `Params` -> `datalens-tabs/Params.js`
- `Sources` -> `datalens-tabs/Sources.js`
- `Controls` -> `datalens-tabs/Controls.js`
- `Prepare` -> `datalens-tabs/Prepare.js`

## Почему нужен current-server файл

На `http://ai360.velkerr.ru:40186` уже работает endpoint:

```text
POST /predict
```

Endpoint `/predict-preset` на этом сервере пока не развернут, поэтому
`datalens-editor-current-server.js` сам собирает полный payload по выбранному
пресету и отправляет его в `/predict`.

## Если появилась ошибка Path in the wrong format

Проверь вкладку `Sources`. Для подключения, где URL path пустой, должно быть:

```js
path: "/predict",
```

Если ты уже указал `/predict` в поле URL path самого API Connector, тогда
во вкладке `Sources` замени путь на:

```js
path: "/",
```

Лучший вариант — оставить URL path в API Connector пустым, а во вкладке
`Sources` использовать `path: "/predict"`.

## Проверенные пресеты

- `eda_cashback`
- `taxi_discount`
- `lavka_points`
- `market_cashback`

## Чарт с картинкой correlation_encoded_heatmap

DataLens не может взять картинку напрямую из локального пути вида
`C:\Users\...\correlation_output\correlation_encoded_heatmap.png`. Картинка
должна быть либо доступна по URL, либо встроена в код чарта как base64.

Сейчас файл уже лежит в проекте здесь:

```text
correlation_output/correlation_encoded_heatmap.png
```

Для отдельного Editor-чарта с этой картинкой:

1. Создай Editor chart / Advanced chart в DataLens.
2. API Connector для этого чарта не нужен.
3. Вставь файлы из папки `datalens-heatmap-tabs` по вкладкам:

- `Meta` -> `datalens-heatmap-tabs/Meta.json`
- `Params` -> `datalens-heatmap-tabs/Params.js`
- `Sources` -> `datalens-heatmap-tabs/Sources.js`
- `Controls` -> `datalens-heatmap-tabs/Controls.js`
- `Prepare` -> `datalens-heatmap-tabs/Prepare.js`

То же самое собрано одним файлом в `datalens-heatmap-editor.js`.

Текущая версия `Prepare.js` уже содержит PNG внутри строки
`data:image/png;base64,...`, поэтому DataLens не ходит за картинкой на внешний
сервер и не зависит от `http` / `https`.
