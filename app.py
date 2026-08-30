import streamlit as st
import asyncio
from streamlit_autorefresh 
import st_autorefresh
import websockets
import json
import requests
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import threading
import queue

API_URL = "https://web-production-015c9.up.railway.app"
WS_URL = "wss://web-production-015c9.up.railway.app/stream"

st.set_page_config(page_title="E-Commerce Anomaly Monitor", layout="wide")
st.title("🛡️ Real-Time E-Commerce Anomaly Detection")

# --- Shared queue to pass WebSocket messages into Streamlit's main thread ---
if "msg_queue" not in st.session_state:
    st.session_state.msg_queue = queue.Queue()
if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "ws_started" not in st.session_state:
    st.session_state.ws_started = False

def ws_listener(q):
    """Runs in a background thread, listens to the WebSocket, pushes messages into the queue."""
    async def listen():
        async with websockets.connect(WS_URL) as ws:
            while True:
                msg = await ws.recv()
                q.put(json.loads(msg))
    asyncio.run(listen())

if not st.session_state.ws_started:
    thread = threading.Thread(target=ws_listener, args=(st.session_state.msg_queue,), daemon=True)
    thread.start()
    st.session_state.ws_started = True

# --- Sidebar controls ---
st.sidebar.header("Controls")

col_a, col_b = st.sidebar.columns(2)
if col_a.button("▶ Start"):
    requests.post(f"{API_URL}/simulate/start")
if col_b.button("⏹ Stop"):
    requests.post(f"{API_URL}/simulate/stop")

threshold = st.sidebar.slider("Sensitivity Threshold", 0.0, 1.0, 0.55, 0.01)
if st.sidebar.button("Apply Threshold"):
    requests.post(f"{API_URL}/threshold", json={"threshold": threshold})
    st.sidebar.success(f"Threshold set to {threshold}")

st.sidebar.markdown("---")
if st.sidebar.button("⚡ Simulate Attack"):
    resp = requests.post(f"{API_URL}/replay-attack").json()
    if resp.get("was_caught"):
        st.sidebar.success(f"Attack injected — CAUGHT (score: {resp['score']:.3f})")
    else:
        st.sidebar.warning(f"Attack injected — missed (score: {resp['score']:.3f})")

# --- Drain queue into session state ---
while not st.session_state.msg_queue.empty():
    st.session_state.transactions.append(st.session_state.msg_queue.get())
st.session_state.transactions = st.session_state.transactions[-200:]  # keep last 200

# --- Top stats row ---
try:
    stats = requests.get(f"{API_URL}/stats").json()
except Exception:
    stats = {"running": False, "total_processed": 0, "total_flagged": 0, "loss_prevented": 0.0}

c1, c2, c3, c4 = st.columns(4)
c1.metric("Status", "🟢 Running" if stats["running"] else "🔴 Stopped")
c2.metric("Transactions Processed", stats["total_processed"])
c3.metric("Anomalies Flagged", stats["total_flagged"])
c4.metric("💰 Estimated Loss Prevented", f"${stats['loss_prevented']:,.2f}")

# --- Live chart ---
st.markdown("### Live Transaction Stream")
if st.session_state.transactions:
    df = pd.DataFrame(st.session_state.transactions)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    fig = go.Figure()
    normal = df[~df["is_anomaly"]]
    anomalies = df[df["is_anomaly"]]

    fig.add_trace(go.Scatter(x=normal["timestamp"], y=normal["anomaly_score"], mode="markers",
                              marker=dict(color="green", size=8), name="Normal"))
    fig.add_trace(go.Scatter(x=anomalies["timestamp"], y=anomalies["anomaly_score"], mode="markers",
                              marker=dict(color="red", size=12, symbol="x"), name="Anomaly"))
    fig.add_hline(y=stats.get("threshold", 0.55), line_dash="dash", line_color="orange",
                  annotation_text="Threshold")
    fig.update_layout(yaxis_title="Anomaly Score", xaxis_title="Time", height=400)
    st.plotly_chart(fig, use_container_width=True)

    # --- Alert list ---
    st.markdown("### Recent Alerts")
    alert_df = anomalies[["timestamp", "customer_id", "amount", "location", "anomaly_score"]].tail(15).sort_values("timestamp", ascending=False)
    st.dataframe(alert_df, use_container_width=True)
else:
    st.info("No transactions yet — click ▶ Start in the sidebar to begin the live stream.")

# --- Auto-refresh every 2 seconds (session-state safe) ---
st_autorefresh(interval=2000, key="datarefresh")
