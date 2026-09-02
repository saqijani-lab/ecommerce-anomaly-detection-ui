# Real-Time E-Commerce Anomaly Detection Live Dashboard

A Streamlit dashboard that connects over WebSocket to the (https://github.com/saqijani-lab/ecommerce-anomaly-detection), visualising transactions as they're scored in real time.

## What It Does

 **Live-updating chart**  every transaction streamed from the API is plotted by anomaly score as it arrives, colour-coded green (normal) or red X (anomaly)
 **Adjustable sensitivity**  a threshold slider lets you tune how aggressive the detection is, applied live without restarting the stream
 **Attack simulation**  a "Simulate Attack" button injects a known fraud pattern into the live stream on demand, so the detection can be demonstrated working in real time rather than waiting passively for an anomaly to occur naturally
 **Running business metrics**  transactions processed, anomalies flagged, and an estimated dollar value of loss prevented, updating live
 **Recent alerts table**  a sortable log of flagged transactions with customer, amount, location, and anomaly score

## Why This Matters

Most anomaly-detection demos show a static chart of historical results. This dashboard demonstrates the harder, more realistic version: a live system processing an ongoing stream, where a human operator can adjust sensitivity and see the consequences immediately — closer to how a real fraud-monitoring tool is actually operated.

## Tech Stack

Streamlit, `websockets` (for the live connection to the FastAPI backend), Plotly, Pandas, `streamlit-autorefresh`.

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Update the `API_URL` and `WS_URL` variables in `app.py` to point at your own deployed backend.

## Live Demo

Deployed at:[https://ecommerce-anomaly-detection-ui-777.streamlit.app/]
Backend API: [ecommerce-anomaly-detection](https://github.com/saqijani-lab/ecommerce-anomaly-detection)

## A Note on Debugging This Build

The WebSocket connection initially failed silently with a 404 error — traced back to Uvicorn running without WebSocket protocol support installed (`uvicorn[standard]` and `websockets` were missing from the backend's dependencies). This is a common but easy-to-miss deployment pitfall: plain HTTP routes work fine without it, masking the issue until a WebSocket route is actually tested
