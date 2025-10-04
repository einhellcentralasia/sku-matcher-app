import os, sys, platform
import pandas as pd
import streamlit as st

st.title("✅ Hello from Streamlit (control test)")
st.write({
    "python": sys.version.split()[0],
    "platform": platform.platform(),
    "streamlit": st.__version__,
    "pandas": pd.__version__,
})
st.subheader("Repo files in '.'")
st.write(sorted(os.listdir(".")))
st.success("If you see this screen, the platform is fine. The issue is in app.py or its deps.")
