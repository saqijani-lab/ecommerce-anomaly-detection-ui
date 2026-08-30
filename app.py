import streamlit as st
from streamlit_autorefresh import st_autorefresh
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

st.title("🛡️ Real-Time E-Commerce Anomaly Detection")

# ... (the full instrumented WebSocket/queue block goes here) ...

st.caption(f"WebSocket status: {st.session_state.ws_status_holder['status']}")

# --- Shared queue to pass WebSocket messages into Streamlit's main thread ---
if "msg_queue" not in st.session_state:
    st.session_state.msg_queue = queue.Queue()
if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "ws_started" not in st.session_state:
    st.session_state.ws_started = False
if "ws_status" not in st.session_state:
    st.session_state.ws_status = "not started"

def ws_listener(q, status_holder):
    async def listen():
        try:
            status_holder["status"] = "connecting"
            async with websockets.connect(WS_URL) as ws:
                status_holder["status"] = "connected"
                while True:
                    msg = await ws.recv()
                    q.put(json.loads(msg))
        except Exception as e:
            status_holder["status"] = f"error: {repr(e)}"

    while True:
        asyncio.run(listen())
        status_holder["status"] += " (reconnecting...)"

if "ws_status_holder" not in st.session_state:
    st.session_state.ws_status_holder = {"status": "not started"}

if not st.session_state.ws_started:
    thread = threading.Thread(
        target=ws_listener,
        args=(st.session_state.msg_queue, st.session_state.ws_status_holder),
        daemon=True
    )
    thread.start()
    st.session_state.ws_started = True
