const MODEL_RESPONSE_PLACEHOLDER = {
  takeProbability: 0.64,
  useProbability: 0.41,
};

const PREDICT_ENDPOINT = "/predict";

const serviceInterestMap = {
  eda: "food_delivery_interest",
  lavka: "grocery_delivery_interest",
  taxi: "taxi_usage_frequency",
  market: "marketplace_interest",
};

const scoreByLevel = {
  low: 0,
  medium: 0.5,
  high: 1,
  heavy: 1,
};

const form = document.querySelector("#prediction-form");
const resultArray = document.querySelector("#result-array");
const takeProbability = document.querySelector("#take-probability");
const useProbability = document.querySelector("#use-probability");
const payloadEditor = document.querySelector("#payload-editor");
const payloadError = document.querySelector("#payload-error");

let isSyncingPayload = false;
let latestPredictionRequest = 0;

function clampProbability(value) {
  return Math.min(0.99, Math.max(0.01, Number(value.toFixed(2))));
}

function buildPayload(formData) {
  return {
    user_id: Number(formData.get("user_id")),
    income: formData.get("income"),
    age: formData.get("age"),
    city: formData.get("city"),
    device_type: formData.get("device_type"),
    mobile_os: formData.get("mobile_os"),
    internet_usage: formData.get("internet_usage"),
    online_shopping_frequency: formData.get("online_shopping_frequency"),
    promo_sensitivity: formData.get("promo_sensitivity"),
    preferred_payment_method: formData.get("preferred_payment_method"),
    subscription_user: formData.has("subscription_user"),
    food_delivery_interest: formData.get("food_delivery_interest"),
    grocery_delivery_interest: formData.get("grocery_delivery_interest"),
    taxi_usage_frequency: formData.get("taxi_usage_frequency"),
    marketplace_interest: formData.get("marketplace_interest"),
    offer_service_name: formData.get("offer_service_name"),
    offer_surface: formData.get("offer_surface"),
    offer_type: formData.get("offer_type"),
    offer_amount: Number(formData.get("offer_amount")),
    offer_cac: Number(formData.get("offer_cac")),
    percent_discount: Number(formData.get("offer_amount")),
  };
}

function updateFormFromPayload(payload) {
  Object.entries(payload).forEach(([key, value]) => {
    const field = form.elements.namedItem(key);

    if (!field) {
      return;
    }

    if (field.type === "checkbox") {
      field.checked = value === true || value === "true" || value === "True";
      return;
    }

    field.value = String(value);
  });
}

function localPredictOfferResponse(payload) {
  const serviceInterestField = serviceInterestMap[payload.offer_service_name];
  const serviceInterest = scoreByLevel[payload[serviceInterestField]] ?? 0.35;
  const shoppingScore = scoreByLevel[payload.online_shopping_frequency] ?? 0.35;
  const promoScore = scoreByLevel[payload.promo_sensitivity] ?? 0.35;
  const amountScore = Math.min(payload.offer_amount / 50, 1);
  const cacScore = Math.min(payload.offer_cac / 900, 1);

  const placeholderBias =
    MODEL_RESPONSE_PLACEHOLDER.takeProbability -
    MODEL_RESPONSE_PLACEHOLDER.useProbability;

  const take = clampProbability(
    0.22 +
      serviceInterest * 0.24 +
      shoppingScore * 0.16 +
      promoScore * 0.12 +
      amountScore * 0.08 -
      cacScore * 0.03 +
      (payload.subscription_user ? 0.08 : 0) +
      placeholderBias * 0.08,
  );

  const used = clampProbability(
    take * 0.58 +
      serviceInterest * 0.16 +
      (payload.offer_surface === "mission" ? 0.06 : 0) +
      (payload.offer_type === "cashback" ? 0.04 : 0) -
      cacScore * 0.02,
  );

  return [take, Math.min(take, used)];
}

async function predictOfferResponse(payload) {
  const response = await fetch(PREDICT_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`API вернул статус ${response.status}`);
  }

  const prediction = await response.json();

  if (
    !Array.isArray(prediction) ||
    prediction.length !== 2 ||
    prediction.some((item) => typeof item !== "number")
  ) {
    throw new Error("API должен вернуть массив из двух чисел.");
  }

  return prediction;
}

async function renderPrediction() {
  const requestId = ++latestPredictionRequest;
  const payload = buildPayload(new FormData(form));
  let prediction;

  try {
    prediction = await predictOfferResponse(payload);
  } catch (error) {
    prediction = localPredictOfferResponse(payload);
    payloadError.textContent = `API недоступен, использована локальная заглушка: ${error.message}`;
  }

  if (requestId !== latestPredictionRequest) {
    return;
  }

  resultArray.value = `[${prediction.map((item) => item.toFixed(2)).join(", ")}]`;
  takeProbability.textContent = `${Math.round(prediction[0] * 100)}%`;
  useProbability.textContent = `${Math.round(prediction[1] * 100)}%`;

  if (!isSyncingPayload) {
    payloadEditor.value = JSON.stringify(payload, null, 2);
  }

  if (!payloadError.textContent.startsWith("API недоступен")) {
    payloadError.textContent = "";
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  renderPrediction();
});

form.addEventListener("input", () => {
  isSyncingPayload = false;
  renderPrediction();
});

payloadEditor.addEventListener("input", () => {
  isSyncingPayload = true;

  try {
    const payload = JSON.parse(payloadEditor.value);

    if (!payload || Array.isArray(payload) || typeof payload !== "object") {
      throw new Error("Payload должен быть JSON-объектом.");
    }

    updateFormFromPayload(payload);
    payloadError.textContent = "";
    renderPrediction();
  } catch (error) {
    payloadError.textContent = error.message;
  } finally {
    isSyncingPayload = false;
  }
});

renderPrediction();
