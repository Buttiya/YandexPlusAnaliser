from __future__ import annotations

import json
import math
import os
from datetime import date, datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

try:
    from catboost import CatBoostClassifier, Pool
except ImportError:
    CatBoostClassifier = None
    Pool = None


ROOT = Path(__file__).resolve().parent
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
TAKEN_MODEL_PATH = Path(
    os.getenv(
        "TAKEN_MODEL_PATH",
        ROOT.parent / "yandex_plus_ml" / "melanholy" / "my-plus-main" / "artifacts" / "offer_taken_catboost.cbm",
    )
)
USED_MODEL_PATH = Path(
    os.getenv(
        "USED_MODEL_PATH",
        ROOT.parent / "yandex_plus_ml" / "melanholy" / "my-plus-main" / "artifacts" / "offer_used_catboost.cbm",
    )
)

_MODELS: dict[str, Any] = {}
_MODEL_LOAD_ERRORS: dict[str, str] = {}

MODEL_RESPONSE_PLACEHOLDER = {
    "takeProbability": 0.64,
    "useProbability": 0.41,
}

PRESET_PAYLOADS: dict[str, dict[str, Any]] = {
    "eda_cashback": {
        "user_id": 101,
        "income": "middle",
        "age": "25-30",
        "city": "capitals",
        "device_type": "mobile",
        "mobile_os": "ios",
        "internet_usage": "heavy",
        "online_shopping_frequency": "high",
        "promo_sensitivity": "high",
        "preferred_payment_method": "card",
        "subscription_user": True,
        "food_delivery_interest": "high",
        "grocery_delivery_interest": "medium",
        "taxi_usage_frequency": "medium",
        "marketplace_interest": "high",
        "offer_service_name": "eda",
        "offer_surface": "selector",
        "offer_type": "cashback",
        "offer_amount": 29,
        "offer_cac": 300,
        "percent_discount": 15,
    },
    "taxi_discount": {
        "user_id": 102,
        "income": "middle",
        "age": "30-40",
        "city": "million_plus",
        "device_type": "mobile",
        "mobile_os": "android",
        "internet_usage": "heavy",
        "online_shopping_frequency": "medium",
        "promo_sensitivity": "medium",
        "preferred_payment_method": "sbp",
        "subscription_user": False,
        "food_delivery_interest": "medium",
        "grocery_delivery_interest": "low",
        "taxi_usage_frequency": "high",
        "marketplace_interest": "medium",
        "offer_service_name": "taxi",
        "offer_surface": "selector",
        "offer_type": "discount",
        "offer_amount": 20,
        "offer_cac": 260,
        "percent_discount": 20,
    },
    "lavka_points": {
        "user_id": 103,
        "income": "high",
        "age": "30-40",
        "city": "capitals",
        "device_type": "mobile",
        "mobile_os": "ios",
        "internet_usage": "heavy",
        "online_shopping_frequency": "high",
        "promo_sensitivity": "medium",
        "preferred_payment_method": "card",
        "subscription_user": True,
        "food_delivery_interest": "high",
        "grocery_delivery_interest": "high",
        "taxi_usage_frequency": "medium",
        "marketplace_interest": "medium",
        "offer_service_name": "lavka",
        "offer_surface": "mission",
        "offer_type": "points",
        "offer_amount": 35,
        "offer_cac": 340,
        "percent_discount": 18,
    },
    "market_cashback": {
        "user_id": 104,
        "income": "middle",
        "age": "40-50",
        "city": "regional",
        "device_type": "desktop",
        "mobile_os": "other",
        "internet_usage": "medium",
        "online_shopping_frequency": "high",
        "promo_sensitivity": "high",
        "preferred_payment_method": "card",
        "subscription_user": False,
        "food_delivery_interest": "low",
        "grocery_delivery_interest": "medium",
        "taxi_usage_frequency": "low",
        "marketplace_interest": "high",
        "offer_service_name": "market",
        "offer_surface": "push",
        "offer_type": "cashback",
        "offer_amount": 40,
        "offer_cac": 420,
        "percent_discount": 25,
    },
}

PRESET_TITLES = {
    "eda_cashback": "Еда: кешбэк в селекторе",
    "taxi_discount": "Такси: скидка в селекторе",
    "lavka_points": "Лавка: баллы в миссии",
    "market_cashback": "Маркет: кешбэк в push",
}

SERVICE_INTEREST_MAP = {
    "eda": "food_delivery_interest",
    "lavka": "grocery_delivery_interest",
    "taxi": "taxi_usage_frequency",
    "market": "marketplace_interest",
}

SCORE_BY_LEVEL = {
    "missing": 0,
    "low": 0,
    "light": 0.25,
    "medium": 0.5,
    "high": 1,
    "heavy": 1,
}

NUMERIC_FEATURES = {
    "offer.percent_discount",
    "offer.percent_discount_log",
    "user.total_transactions_before_offer",
    "user.same_service_transactions_before_offer",
    "user.total_offers_before_offer",
    "user.same_service_offers_before_offer",
    "user.taken_offers_before_offer",
    "user.same_service_taken_offers_before_offer",
    "user.used_offers_before_offer",
    "user.same_service_used_offers_before_offer",
    "user.offer_index",
    "user.service_offer_index",
    "user.taken_rate_before_offer",
    "user.same_service_taken_rate_before_offer",
    "user.used_rate_before_offer",
    "user.same_surface_taken_rate_before_offer",
    "user.same_offer_type_taken_rate_before_offer",
    "user.same_service_surface_taken_rate_before_offer",
    "user.same_service_offer_type_taken_rate_before_offer",
    "user.same_service_surface_type_taken_rate_before_offer",
    "user.service_transaction_share_before_offer",
    "user.current_service_interest_score",
    "user.market_interest_mean_score",
    "offer.days_since_last_event",
    "offer.days_since_last_same_service_event",
    "offer.days_since_last_offer",
    "offer.days_since_last_same_service_offer",
    "offer.day_of_month",
}

SHOPPING_CATEGORY_GROUPS = {
    "eda": ["food_delivery_interest"],
    "lavka": ["grocery_delivery_interest"],
    "taxi": ["taxi_usage_frequency"],
    "market": [
        "marketplace_interest",
        "fashion_interest",
        "beauty_interest",
        "auto_interest",
        "flowers_interest",
        "pets_goods_interest",
        "electronics_interest",
        "home_repair_interest",
        "sports_interest",
        "kids_products_interest",
    ],
}

SHOPPING_PROPERTY_TO_SERVICE = {
    property_name: service
    for service, property_names in SHOPPING_CATEGORY_GROUPS.items()
    for property_name in property_names
}

MARKET_INTEREST_FIELDS = SHOPPING_CATEGORY_GROUPS["market"]


def clamp_probability(value: float) -> float:
    return min(0.99, max(0.01, round(value, 2)))


def number(value: Any, default: float = 0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_category(value: Any) -> str:
    if value is None or value == "":
        return "missing"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip().lower().replace(" ", "_")


def parse_offer_date(value: Any) -> date:
    if not value:
        return date.today()
    text = str(value)
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text[: len(fmt)], fmt).date()
        except ValueError:
            continue
    return date.today()


def safe_rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def discount_bucket(percent_discount: float) -> str:
    if percent_discount < 5:
        return "00_04"
    if percent_discount < 10:
        return "05_09"
    if percent_discount < 15:
        return "10_14"
    if percent_discount < 20:
        return "15_19"
    if percent_discount < 25:
        return "20_24"
    return "25_plus"


def interest_score(value: Any) -> float:
    return SCORE_BY_LEVEL.get(normalize_category(value), 0.0)


def service_interest_field(service_name: str) -> str:
    return SERVICE_INTEREST_MAP.get(service_name, "marketplace_interest")


def service_family(service_name: str) -> str:
    if service_name == "eda":
        return "food"
    if service_name in {"lavka", "x5", "azbuka"}:
        return "grocery"
    if service_name in {"market", "lamoda", "letual"}:
        return "market"
    if service_name == "taxi":
        return "taxi"
    return "other"


def load_model(name: str, path: Path) -> Any:
    if name in _MODELS or name in _MODEL_LOAD_ERRORS:
        return _MODELS.get(name)

    if CatBoostClassifier is None or Pool is None:
        _MODEL_LOAD_ERRORS[name] = "catboost is not installed"
        return None

    if not path.exists():
        _MODEL_LOAD_ERRORS[name] = f"model file not found: {path}"
        return None

    model = CatBoostClassifier()
    model.load_model(str(path))
    _MODELS[name] = model
    return model


def build_model_row(payload: dict[str, Any], feature_names: list[str]) -> list[Any]:
    user_properties = {
        key: value
        for key, value in payload.items()
        if not key.startswith("offer_") and key not in {"user_id"}
    }
    service_name = normalize_category(payload.get("offer_service_name"))
    offer_surface = normalize_category(payload.get("offer_surface"))
    offer_type = normalize_category(payload.get("offer_type"))
    offer_date = parse_offer_date(payload.get("offer_date") or payload.get("date"))
    percent_discount = number(payload.get("percent_discount"), 0.0)
    percent_discount_bucket = discount_bucket(percent_discount)
    current_service_interest = normalize_category(
        user_properties.get(service_interest_field(service_name))
    )
    market_interest_mean_score = sum(
        interest_score(user_properties.get(field_name))
        for field_name in MARKET_INTEREST_FIELDS
    ) / len(MARKET_INTEREST_FIELDS)

    user_feature_values = {
        f"user.{key}": normalize_category(value)
        for key, value in sorted(user_properties.items())
    }
    for property_name, service in SHOPPING_PROPERTY_TO_SERVICE.items():
        value = normalize_category(user_properties.get(property_name))
        user_feature_values[f"user_service.{service}.{property_name}"] = value

    numeric_values = {
        "offer.percent_discount": percent_discount,
        "offer.percent_discount_log": math.log1p(percent_discount),
        "user.total_transactions_before_offer": 0,
        "user.same_service_transactions_before_offer": 0,
        "user.total_offers_before_offer": 0,
        "user.same_service_offers_before_offer": 0,
        "user.taken_offers_before_offer": 0,
        "user.same_service_taken_offers_before_offer": 0,
        "user.used_offers_before_offer": 0,
        "user.same_service_used_offers_before_offer": 0,
        "user.offer_index": 1,
        "user.service_offer_index": 1,
        "user.taken_rate_before_offer": safe_rate(0, 0),
        "user.same_service_taken_rate_before_offer": safe_rate(0, 0),
        "user.used_rate_before_offer": safe_rate(0, 0),
        "user.same_surface_taken_rate_before_offer": safe_rate(0, 0),
        "user.same_offer_type_taken_rate_before_offer": safe_rate(0, 0),
        "user.same_service_surface_taken_rate_before_offer": safe_rate(0, 0),
        "user.same_service_offer_type_taken_rate_before_offer": safe_rate(0, 0),
        "user.same_service_surface_type_taken_rate_before_offer": safe_rate(0, 0),
        "user.service_transaction_share_before_offer": safe_rate(0, 0),
        "user.current_service_interest_score": interest_score(current_service_interest),
        "user.market_interest_mean_score": market_interest_mean_score,
        "offer.days_since_last_event": 9999.0,
        "offer.days_since_last_same_service_event": 9999.0,
        "offer.days_since_last_offer": 9999.0,
        "offer.days_since_last_same_service_offer": 9999.0,
        "offer.day_of_month": offer_date.day,
    }
    categorical_values = {
        "offer.service_name": service_name,
        "offer.service_family": service_family(service_name),
        "offer.surface": offer_surface,
        "offer.offer_type": offer_type,
        "offer.discount_bucket": percent_discount_bucket,
        "offer.day_of_week": str(offer_date.weekday()),
        "cross.service_surface": f"{service_name}|{offer_surface}",
        "cross.service_offer_type": f"{service_name}|{offer_type}",
        "cross.surface_offer_type": f"{offer_surface}|{offer_type}",
        "cross.service_surface_offer_type": f"{service_name}|{offer_surface}|{offer_type}",
        "cross.service_discount_bucket": f"{service_name}|{percent_discount_bucket}",
        "cross.promo_discount_bucket": (
            f"{normalize_category(user_properties.get('promo_sensitivity'))}|"
            f"{percent_discount_bucket}"
        ),
        "cross.promo_service": (
            f"{normalize_category(user_properties.get('promo_sensitivity'))}|{service_name}"
        ),
        "cross.age_service": f"{normalize_category(user_properties.get('age'))}|{service_name}",
        "cross.city_service": f"{normalize_category(user_properties.get('city'))}|{service_name}",
        "cross.device_service": (
            f"{normalize_category(user_properties.get('device_type'))}|{service_name}"
        ),
        "cross.os_service": f"{normalize_category(user_properties.get('mobile_os'))}|{service_name}",
        "cross.subscription_service": (
            f"{normalize_category(user_properties.get('subscription_user'))}|{service_name}"
        ),
        "cross.payment_service": (
            f"{normalize_category(user_properties.get('preferred_payment_method'))}|{service_name}"
        ),
        "cross.current_service_interest": f"{service_name}|{current_service_interest}",
        "history.last_event_kind": "none",
        "history.last_event_service": "none",
        "history.last_same_service_event_kind": "none",
        "history.last_offer_type": "none",
        "history.last_offer_surface": "none",
        "history.last_same_service_offer_type": "none",
        "history.last_same_service_surface": "none",
    }

    values = {**user_feature_values, **categorical_values, **numeric_values}
    return [
        number(values.get(name), 0.0) if name in NUMERIC_FEATURES else normalize_category(values.get(name))
        for name in feature_names
    ]


def predict_one_model(payload: dict[str, Any], name: str, path: Path) -> float | None:
    model = load_model(name, path)
    if model is None:
        return None

    feature_names = list(model.feature_names_)
    row = build_model_row(payload, feature_names)
    categorical_features = [
        index for index, feature_name in enumerate(feature_names) if feature_name not in NUMERIC_FEATURES
    ]
    pool = Pool(
        data=[row],
        cat_features=categorical_features,
        feature_names=feature_names,
    )
    return clamp_probability(float(model.predict_proba(pool)[0][1]))


def predict_offer_response_with_model(payload: dict[str, Any]) -> list[float] | None:
    take = predict_one_model(payload, "taken", TAKEN_MODEL_PATH)
    if take is None:
        return None

    used = predict_one_model(payload, "used", USED_MODEL_PATH)
    if used is None:
        used = clamp_probability(
            take * 0.68
            + (0.05 if payload.get("offer_type") == "cashback" else 0)
            + (0.04 if payload.get("offer_surface") == "mission" else 0)
        )
    return [take, min(take, used)]


def offer_amount_value(payload: dict[str, Any]) -> float:
    if payload.get("percent_discount") not in {None, ""}:
        return number(payload.get("percent_discount"))
    return number(payload.get("offer_amount"))


def adjust_prediction_for_offer_controls(
    payload: dict[str, Any],
    prediction: list[float],
) -> list[float]:
    amount_score = min(max(offer_amount_value(payload), 0), 50) / 50
    cac_score = min(max(number(payload.get("offer_cac")), 0), 900) / 900

    take_delta = (amount_score - 0.3) * 0.12 - cac_score * 0.05
    used_delta = (amount_score - 0.3) * 0.08 - cac_score * 0.03

    take = clamp_probability(prediction[0] + take_delta)
    used = clamp_probability(prediction[1] + used_delta)
    return [take, min(take, used)]


def predict_offer_response(payload: dict[str, Any]) -> list[float]:
    model_prediction = predict_offer_response_with_model(payload)
    if model_prediction is not None:
        return adjust_prediction_for_offer_controls(payload, model_prediction)

    service = str(payload.get("offer_service_name", ""))
    service_interest_field = SERVICE_INTEREST_MAP.get(service)
    service_interest = SCORE_BY_LEVEL.get(str(payload.get(service_interest_field)), 0.35)
    shopping_score = SCORE_BY_LEVEL.get(
        str(payload.get("online_shopping_frequency")),
        0.35,
    )
    promo_score = SCORE_BY_LEVEL.get(str(payload.get("promo_sensitivity")), 0.35)
    amount_score = min(offer_amount_value(payload) / 50, 1)
    cac_score = min(number(payload.get("offer_cac")) / 900, 1)

    placeholder_bias = (
        MODEL_RESPONSE_PLACEHOLDER["takeProbability"]
        - MODEL_RESPONSE_PLACEHOLDER["useProbability"]
    )

    take = clamp_probability(
        0.22
        + service_interest * 0.24
        + shopping_score * 0.16
        + promo_score * 0.12
        + amount_score * 0.08
        - cac_score * 0.03
        + (0.08 if bool(payload.get("subscription_user")) else 0)
        + placeholder_bias * 0.08
    )

    used = clamp_probability(
        take * 0.58
        + service_interest * 0.16
        + (0.06 if payload.get("offer_surface") == "mission" else 0)
        + (0.04 if payload.get("offer_type") == "cashback" else 0)
        - cac_score * 0.02
    )

    return [take, min(take, used)]


def normalize_preset(value: Any) -> str:
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value or "eda_cashback").strip()


def predict_preset_response(request_payload: dict[str, Any]) -> dict[str, Any]:
    preset = normalize_preset(request_payload.get("preset"))
    if preset not in PRESET_PAYLOADS:
        raise ValueError(
            f"Unknown preset '{preset}'. Available presets: {', '.join(PRESET_PAYLOADS)}"
        )

    payload = {**PRESET_PAYLOADS[preset], **request_payload.get("payload", {})}
    prediction = predict_offer_response(payload)
    take_probability, use_probability = prediction
    recommendation = (
        "Сильный офер: можно показывать в приоритетном месте."
        if take_probability >= 0.7
        else "Средний офер: стоит проверить аудиторию или размер выгоды."
        if take_probability >= 0.45
        else "Слабый офер: лучше заменить механику или сегмент."
    )

    return {
        "preset": preset,
        "title": PRESET_TITLES[preset],
        "takeProbability": take_probability,
        "useProbability": use_probability,
        "takePercent": round(take_probability * 100),
        "usePercent": round(use_probability * 100),
        "recommendation": recommendation,
        "payload": payload,
        "raw": prediction,
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)

        if self.path == "/":
            self.path = "/index.html"

        if parsed_url.path == "/health":
            self.send_json({
                "status": "ok",
                "models": {
                    "taken": {
                        "loaded": load_model("taken", TAKEN_MODEL_PATH) is not None,
                        "path": str(TAKEN_MODEL_PATH),
                        "error": _MODEL_LOAD_ERRORS.get("taken"),
                    },
                    "used": {
                        "loaded": load_model("used", USED_MODEL_PATH) is not None,
                        "path": str(USED_MODEL_PATH),
                        "error": _MODEL_LOAD_ERRORS.get("used"),
                    },
                },
            })
            return

        if parsed_url.path == "/predict-ui":
            try:
                query = parse_qs(parsed_url.query)
                self.send_json(predict_preset_response({
                    "preset": query.get("preset", ["eda_cashback"])[0],
                }))
            except ValueError as error:
                self.send_json(
                    {"error": str(error)},
                    status=HTTPStatus.BAD_REQUEST,
                )
            return

        super().do_GET()

    def do_POST(self) -> None:
        parsed_url = urlparse(self.path)
        if parsed_url.path not in {"/predict", "/predict-preset"}:
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(raw_body or "{}")
            query = parse_qs(parsed_url.query)

            if not isinstance(payload, dict):
                raise ValueError("Request body must be a JSON object")

            if parsed_url.path == "/predict-preset":
                if "preset" not in payload and "preset" in query:
                    payload["preset"] = query["preset"][0]
                self.send_json(predict_preset_response(payload))
                return

            self.send_json(predict_offer_response(payload))
        except json.JSONDecodeError:
            self.send_json(
                {"error": "Invalid JSON body"},
                status=HTTPStatus.BAD_REQUEST,
            )
        except ValueError as error:
            self.send_json(
                {"error": str(error)},
                status=HTTPStatus.BAD_REQUEST,
            )

    def send_json(self, data: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving site and API on http://{HOST}:{PORT}")
    server.serve_forever()
