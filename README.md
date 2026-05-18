# Yandex Plus Offer API Prototype

Локальный прототип сайта и HTTP API для проверки идеи сервиса, который принимает данные пользователя и офера, а возвращает массив из двух чисел:

```json
[0.72, 0.62]
```

Первое число - вероятность того, что пользователь возьмет офер. Второе число - вероятность того, что пользователь воспользуется офером.

## Ссылки

- DataLens: https://datalens.ru/lzhc9vh4fyku5
- DataLens: https://datalens.ru/1f1dufvarbaql
- Демо API: http://ai360.velkerr.ru:40186/

## Что внутри

- `index.html` - разметка страницы и форма ввода данных.
- `styles.css` - стили интерфейса.
- `app.js` - сбор payload, вызов API и вывод результата.
- `server.py` - статический сервер и endpoint `POST /predict`.
- `datalens-editor.js` - готовые JS-сниппеты для вкладок Yandex DataLens Editor.
- `flat_dataset_reduced (1).csv` - плоский датасет, по которому выбраны поля формы.
- `dataset (1).json` - исходный JSON-датасет.

## Локальный запуск

Из папки проекта:

```bash
python server.py
```

После запуска откройте:

```text
http://127.0.0.1:8000/
```

По умолчанию сервер слушает порт `8000`. Порт можно поменять через переменную окружения:

```bash
PORT=40186 python server.py
```

## Формат входных данных

Форма собирает объект с пользовательскими параметрами и параметрами офера:

```json
{
  "user_id": 5,
  "income": "middle",
  "age": "30-40",
  "city": "capitals",
  "device_type": "mobile",
  "mobile_os": "ios",
  "internet_usage": "heavy",
  "online_shopping_frequency": "high",
  "promo_sensitivity": "low",
  "preferred_payment_method": "sbp",
  "subscription_user": false,
  "food_delivery_interest": "high",
  "grocery_delivery_interest": "high",
  "taxi_usage_frequency": "low",
  "marketplace_interest": "high",
  "offer_service_name": "eda",
  "offer_surface": "selector",
  "offer_type": "cashback",
  "offer_amount": 29,
  "offer_cac": 300
}
```

Поля взяты из `flat_dataset_reduced (1).csv`.

Payload справа на странице можно редактировать вручную. Если вставить валидный JSON-объект с полями из формы, соответствующие input/select/checkbox слева обновятся автоматически, а результат пересчитается.

## Формат ответа

API endpoint:

```http
POST /predict
Content-Type: application/json
```

Ответ возвращается как JSON-массив:

```json
[takeProbability, useProbability]
```

Где:

- `takeProbability` - вероятность взятия офера.
- `useProbability` - вероятность использования офера.

Оба значения находятся в диапазоне от `0.01` до `0.99`.

## Endpoint для Yandex DataLens

Для селектора пресетов в DataLens есть отдельный endpoint:

```http
POST /predict-preset
Content-Type: application/json
```

Пример запроса:

```json
{
  "preset": "eda_cashback"
}
```

Доступные пресеты:

- `eda_cashback`
- `taxi_discount`
- `lavka_points`
- `market_cashback`

Ответ возвращается объектом, который удобно отображать в Advanced-чарте DataLens:

```json
{
  "preset": "eda_cashback",
  "title": "Еда: кешбэк в селекторе",
  "takeProbability": 0.73,
  "useProbability": 0.58,
  "takePercent": 73,
  "usePercent": 58,
  "recommendation": "Сильный офер: можно показывать в приоритетном месте.",
  "raw": [0.73, 0.58]
}
```

Код для вкладок `Meta`, `Params`, `Sources`, `Controls` и `Prepare` лежит в `datalens-editor.js`. В DataLens нужно создать API Connector на публичный HTTPS-адрес этого сайта и заменить `YOUR_API_CONNECTION_ID` на ID подключения.

## Где находится заглушка модели

В файле `app.js` есть переменная:

```js
const MODEL_RESPONSE_PLACEHOLDER = {
  takeProbability: 0.64,
  useProbability: 0.41,
};
```

Сейчас итоговый результат считается простой эвристикой в двух местах:

- `server.py` - основная API-логика в `predict_offer_response`.
- `app.js` - локальный fallback `localPredictOfferResponse`, если API недоступен.

Позже основную backend-функцию можно заменить на:

- вызов модели;
- загрузку заранее рассчитанного ответа;
- любую бизнес-логику ранжирования оферов.

## Текущая логика расчета

Заглушка учитывает:

- интерес пользователя к сервису офера;
- частоту онлайн-покупок;
- чувствительность к промо;
- размер офера;
- наличие подписки;
- тип и поверхность офера.

Это не ML-модель, а временная логика, чтобы сайт уже можно было запускать и демонстрировать end-to-end сценарий.

## Подготовка к загрузке в Yandex Cloud

Сейчас проект можно разместить как простой Python-сервис:

```bash
PORT=40186 python server.py
```

Для production-запуска лучше оформить процесс через `systemd`, чтобы сервис автоматически поднимался после перезагрузки сервера.

Если frontend и backend будут на разных доменах, нужно будет отдельно настроить CORS.

## Корреляционная матрица

Для генерации корреляционных матриц по CSV-датасету:

```bash
python generate_correlation_matrix.py
```

Скрипт создаст папку `correlation_output` с файлами:

- `correlation_numeric.csv` - корреляция по числовым и boolean-полям.
- `correlation_encoded.csv` - корреляция после one-hot кодирования категориальных полей.
- `correlation_numeric_sparse.csv` - разреженная числовая матрица: слабые связи скрыты.
- `correlation_encoded_sparse.csv` - разреженная encoded-матрица без `*_missing` и технических связей внутри одного one-hot признака.
- `top_correlations_numeric.csv` - самые сильные пары среди числовых полей.
- `top_correlations_encoded.csv` - самые сильные пары среди encoded-полей.
- `top_correlations_numeric_sparse.csv` - самые сильные пары из разреженной числовой матрицы.
- `top_correlations_encoded_sparse.csv` - самые сильные пары из разреженной encoded-матрицы.
- `correlation_numeric_heatmap.png` - heatmap для числовой матрицы.
- `correlation_encoded_heatmap.png` - heatmap для encoded-матрицы.

По умолчанию heatmap строится по разреженной матрице:

- выкидываются one-hot колонки со значением `missing`;
- выкидываются корреляции между дамми-колонками одного исходного категориального признака;
- скрываются связи с `abs(correlation) < 0.10`;
- на heatmap попадают признаки с самыми сильными связями, а не первые колонки CSV.

Быстрый тест на части данных:

```bash
python generate_correlation_matrix.py --sample-rows 5000
```

Полезные параметры:

```bash
python generate_correlation_matrix.py --method spearman --max-categories 15 --top-n 200
python generate_correlation_matrix.py --heatmap-size 12 --cmap RdYlBu_r
python generate_correlation_matrix.py --sparse-threshold 0.2
python generate_correlation_matrix.py --sparse-threshold 0 --keep-missing-dummies
```
