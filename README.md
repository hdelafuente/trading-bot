# Trading Bot

Un bot de trading automatizado para Binance Futures que implementa estrategias basadas en indicadores técnicos con capacidades de backtesting y visualización.

## 🚀 Características

- **Trading Automatizado**: Ejecuta operaciones automáticas en Binance Futures
- **Backtesting**: Prueba estrategias con datos históricos
- **Dashboard Interactivo**: Visualiza resultados y métricas con Dash
- **Múltiples Indicadores**: MACD, RSI, Stoch RSI, EMA, Bollinger Bands, ADX
- **Gestión de Riesgo**: Stop Loss, Take Profit y gestión de posiciones
- **Métricas Detalladas**: Win ratio, profit factor, drawdown máximo, ROI

## 📋 Requisitos Previos

- Python 3.8+
- Cuenta de Binance con API habilitada para Futures
- API Key y Secret Key de Binance

## 🛠️ Instalación

1. **Clona el repositorio**:
```bash
git clone <repository-url>
cd trading-bot
```

2. **Instala las dependencias**:
```bash
pip install -r requirements.txt
```

3. **Configura las variables de entorno**:
Crea un archivo `.env` en el directorio raíz o configura las variables de entorno:
```bash
export API_KEY="tu_binance_api_key"
export API_SECRET="tu_binance_api_secret"
```

4. **Crea los directorios necesarios**:
```bash
mkdir data results
```

## 📊 Estructura del Proyecto

```
trading-bot/
├── main.py                 # Punto de entrada principal
├── bot.py                  # Lógica principal del bot
├── binance_integration.py  # Integración con Binance API
├── strategy.py             # Estrategias de trading
├── metrics.py              # Cálculo de métricas
├── utils.py                # Utilidades y configuración
├── app.py                  # Dashboard web
├── requirements.txt        # Dependencias
├── data/                   # Datos históricos (CSV)
├── results/                # Resultados de backtests (JSON)
└── README.md
```

## 🎯 Uso

### Comandos Principales

El bot se ejecuta a través de `main.py` con diferentes comandos:

#### 1. Extraer Datos Históricos
```bash
python main.py extract
```
- Descarga datos históricos de los símbolos configurados
- Guarda los datos en formato CSV en el directorio `data/`
- Añade indicadores técnicos automáticamente

#### 2. Ejecutar Backtesting
```bash
python main.py backtest
```
- Ejecuta backtesting de la estrategia configurada
- Genera métricas de rendimiento
- Guarda resultados en `results/` como archivos JSON

#### 3. Trading en Vivo
```bash
python main.py run
```
- **⚠️ CUIDADO**: Ejecuta trading real con dinero real
- Monitorea el mercado cada 2 minutos
- Abre/cierra posiciones automáticamente
- Usa Ctrl+C para detener y ver resumen de trades

### Configuración

Modifica las variables en `utils.py`:

```python
SYMBOLS = ["BTCUSDT", "ETHUSDT"]  # Pares a tradear
TIMEFRAME = "1h"                  # Timeframe de análisis
TP = 0.05                         # Take Profit (5%)
SL = 0.02                         # Stop Loss (2%)
LEVERAGE = 10                     # Apalancamiento
BALANCE = 300                     # Balance inicial para backtest
RISK_BALANCE = 0.3                # % del balance por trade
```

## 📈 Dashboard Web

### Ejecutar el Dashboard
```bash
python app.py
```

El dashboard estará disponible en: `http://localhost:8050`

### Características del Dashboard
- **Selector de Símbolos**: Cambia entre diferentes pares
- **Tabla de Métricas**: ROI, win ratio, profit factor, etc.
- **Gráfico de PnL**: Ganancias/pérdidas por trade
- **Gráfico de Precios**: Precio + indicadores + señales de entrada/salida
- **Gráfico de Balance**: Evolución del balance en el tiempo
- **Tabla de Trades**: Historial detallado de operaciones

## 💾 Almacenamiento de Datos

### Datos Históricos (`data/`)
```
data/
├── BTCUSDT-1h.csv
├── ETHUSDT-1h.csv
└── ...
```

**Formato CSV**:
- `Time`: Timestamp
- `Open`, `High`, `Low`, `Close`: Precios OHLC
- `Volume`: Volumen
- Indicadores técnicos: `macd`, `rsi`, `stoch_rsi`, `ema_200`, etc.

### Resultados de Backtests (`results/`)
```
results/
├── stoch_rsi_ema_200_backtest_results_BTCUSDT.json
├── stoch_rsi_ema_200_backtest_results_ETHUSDT.json
└── ...
```

**Estructura JSON**:
```json
{
  "metrics": {
    "initial_balance": 300.0,
    "final_balance": 450.25,
    "win_ratio": 0.65,
    "average_win": 25.30,
    "average_loss": -12.15,
    "risk_reward_ratio": 2.08,
    "roi": 50.08,
    "max_drawdown": 0.15,
    "profit_factor": 1.85,
    "start_date": "2024-01-01",
    "end_date": "2024-08-30"
  },
  "trades": [
    {
      "entry_date": "2024-01-15T10:00:00",
      "exit_date": "2024-01-15T14:00:00",
      "entry_price": 42500.0,
      "exit_price": 43625.0,
      "qty": 900.0,
      "sign": "buy",
      "tp_price": 44625.0,
      "sl_price": 41650.0,
      "pnl": 23.85,
      "starting_balance": 300.0,
      "final_balance": 323.85
    }
  ],
  "config": {
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "tp": 0.05,
    "sl": 0.02,
    "leverage": 10,
    "balance": 300,
    "risk_balance": 0.3
  }
}
```

## ⚠️ Advertencias Importantes

1. **Trading Real**: El comando `run` usa dinero real. Prueba primero con `backtest`
2. **API Keys**: Nunca compartas tus claves API
3. **Riesgo**: El trading de criptomonedas conlleva riesgo de pérdida total
4. **Backtesting**: Los resultados pasados no garantizan resultados futuros

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo `LICENSE` para detalles.

## 📞 Soporte

Para preguntas o problemas, abre un issue en el repositorio.
