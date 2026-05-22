param(
    [string]$User = "ai360p2026s186",
    [string]$HostName = "ai360.velkerr.ru",
    [string]$RemoteDir = "/home/ai360p2026s/ai360p2026s186/YandexPlusAPI",
    [int]$Port = 40186
)

$ErrorActionPreference = "Stop"

$RemoteTarget = "${User}@${HostName}:${RemoteDir}/"

Write-Host "Uploading app, DataLens snippets, and correlation output to $RemoteTarget"
scp `
    server.py `
    app.js `
    index.html `
    styles.css `
    correlation_heatmap.html `
    datalens-heatmap-editor.js `
    $RemoteTarget

scp -r `
    correlation_output `
    datalens-heatmap-tabs `
    $RemoteTarget

Write-Host "Restarting Python API on port $Port"
$RemoteScript = @'
set -e
cd "__REMOTE_DIR__"
PYTHON="/home/ai360p2026s/ai360p2026s186/yandex_plus_ml/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
  PYTHON="python3"
fi
if command -v lsof >/dev/null 2>&1; then
  PID=$(lsof -ti tcp:__PORT__ || true)
  if [ -n "$PID" ]; then
    kill $PID || true
    sleep 1
  fi
else
  pkill -f "python.*server.py" || true
  sleep 1
fi
PORT=__PORT__ nohup "$PYTHON" server.py > server.log 2>&1 &
sleep 2
curl -sS "http://127.0.0.1:__PORT__/health"
'@
$RemoteScript = $RemoteScript.Replace("__REMOTE_DIR__", $RemoteDir).Replace("__PORT__", [string]$Port)
ssh "${User}@${HostName}" $RemoteScript

Write-Host ""
Write-Host "Checking public /predict response"
$body = @{
    user_id = 5
    income = "middle"
    age = "30-40"
    city = "capitals"
    device_type = "mobile"
    mobile_os = "ios"
    internet_usage = "heavy"
    online_shopping_frequency = "high"
    promo_sensitivity = "low"
    preferred_payment_method = "sbp"
    subscription_user = $false
    food_delivery_interest = "high"
    grocery_delivery_interest = "high"
    taxi_usage_frequency = "low"
    marketplace_interest = "high"
    offer_service_name = "eda"
    offer_surface = "selector"
    offer_type = "cashback"
    offer_amount = 50
    offer_cac = 100
    percent_discount = 50
} | ConvertTo-Json

Invoke-WebRequest `
    -Uri "http://$HostName`:$Port/predict" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body `
    -UseBasicParsing |
    Select-Object -ExpandProperty Content
