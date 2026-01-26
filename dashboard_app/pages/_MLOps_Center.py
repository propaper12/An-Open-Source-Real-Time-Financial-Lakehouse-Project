import streamlit as st
import pandas as pd
import requests
import os
import mlflow
from mlflow.tracking import MlflowClient
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

AIRFLOW_API_URL = os.getenv("AIRFLOW_INTERNAL_API", "http://airflow:8080/api/v1")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_INTERNAL_URI", "http://mlflow_server:5000")

AIRFLOW_UI_URL = os.getenv("AIRFLOW_EXTERNAL_UI", "http://localhost:8081")
MLFLOW_UI_URL = os.getenv("MLFLOW_EXTERNAL_UI", "http://localhost:5000")

AIRFLOW_USER = os.getenv("AIRFLOW_USER", "admin")
AIRFLOW_PASS = os.getenv("AIRFLOW_PASS", "admin")

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
try:
    client = MlflowClient()
except:
    client = None

st.set_page_config(page_title="Enterprise MLOps Studio", layout="wide")

c1, c2 = st.columns([3, 1])
with c1:
    st.title(" Enterprise MLOps Command Center")
    st.markdown(f"""
    **Hızlı Erişim:** [Airflow UI]({AIRFLOW_UI_URL}) 🔗 | [MLflow UI]({MLFLOW_UI_URL}) 🔗
    """)
with c2:
    st.caption("Status: Connected via Docker Network 🐳")

st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader(" Eğitim Başlat")
    with st.form("training_form"):
        target_device = st.text_input("Hedef Sembol", value="BTC-USDT")
        algorithm = st.selectbox("Algoritma", ["LinearRegression", "RandomForestRegressor", "GBTRegressor"])
        epochs = st.slider("Epochs", 10, 100, 20)
        learning_rate = st.number_input("Learning Rate", value=0.01)
        submitted = st.form_submit_button(" Modeli Eğit")

    if submitted:
        dag_id = "crypto_data_pipeline_v2"
        conf = {
            "symbol": target_device,
            "algorithm": algorithm,
            "params": {"epochs": epochs, "lr": learning_rate}
        }
        
        req_url = f"{AIRFLOW_API_URL}/dags/{dag_id}/dagRuns"
        
        try:
            st.info(f"İstek Docker içinden gönderiliyor: `{req_url}`")
            response = requests.post(req_url, json={"conf": conf}, auth=(AIRFLOW_USER, AIRFLOW_PASS))
            
            if response.status_code == 200:
                st.success(f" Başarılı! Run ID: {response.json().get('dag_run_id')}")
            else:
                st.error(f"Hata: {response.status_code}")
                st.write(response.text)
        except Exception as e:
            st.error("Bağlantı Hatası!")
            st.write(e)

with col2:
    st.subheader(" Model Registry")
    tab1, tab2 = st.tabs([" Lider Tablosu", "🕸️ MLflow UI"])
    
    with tab1:
        try:
            experiments = mlflow.search_experiments()
            if not experiments:
                st.warning("Veri yok.")
            else:
                selected_exp = st.selectbox("Deney Seç", [e.name for e in experiments])
                exp_id = [e.experiment_id for e in experiments if e.name == selected_exp][0]
                runs = mlflow.search_runs(experiment_ids=[exp_id], order_by=["metrics.rmse ASC"])
                if not runs.empty:
                     st.dataframe(runs[["params.algorithm", "metrics.rmse", "start_time"]], use_container_width=True)
                else:
                    st.info("Bu deney boş.")
        except Exception as e:
            st.error("MLflow Internal Bağlantı Hatası")
            st.write(e)

    with tab2:
        try:
            components.iframe(MLFLOW_UI_URL, height=700, scrolling=True)
        except:
            st.error("Iframe yüklenemedi.")