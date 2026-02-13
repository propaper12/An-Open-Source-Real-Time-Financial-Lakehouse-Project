import streamlit as st
import pandas as pd
import mlflow
from mlflow.tracking import MlflowClient
import plotly.express as px
import os
from datetime import datetime

#AYARLAR
st.set_page_config(page_title="MLOps Studio", layout="wide")

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_INTERNAL_URI", "http://mlflow:5000")
MLFLOW_EXTERNAL_UI = "http://localhost:5000"

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

#YARDIMCI FONKSİYONLAR 
def extract_algo_name(row):
    """
    Run isimlerinden temiz Algoritma adı çıkarır.
    """
    if pd.notna(row.get('tags.winner_algo')):
        return row['tags.winner_algo'].replace('_', ' ')
    if pd.notna(row.get('params.winner_algo')):
        return row['params.winner_algo'].replace('_', ' ')
        
    run_name = row.get('tags.mlflow.runName', str(row.name))
    if isinstance(run_name, str):
        if "RandomForest" in run_name: return "Random Forest"
        if "Elastic" in run_name: return "ElasticNet Regression" 
        if "Linear" in run_name: return "Linear Regression"
        if "DecisionTree" in run_name: return "Decision Tree"
        if "Gradient" in run_name or "GBT" in run_name: return "Gradient Boosted"
        if "CHAMPION" in run_name: return " CHAMPION MODEL"
    
    return "Unknown Model"

def get_mlflow_data():
    try:
        client = MlflowClient()
        experiment = client.get_experiment_by_name("RealTime_AutoML_League")
        
        if experiment:
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=["start_time DESC"]
            )
            return runs
        return pd.DataFrame()
    except Exception as e:
        st.error(f"MLflow Bağlantı Hatası: {e}")
        return pd.DataFrame()

# ARAYÜZ
st.title(" Enterprise AutoML & Model Performance Analytics")
st.markdown("Bu panel, sistemdeki yapay zeka modellerinin **performans metriklerini, kararlılığını ve şampiyon seçimlerini** analiz eder.")

st.divider()

df_runs = get_mlflow_data()

if not df_runs.empty:
    # VERİ TEMİZLİĞİ
    df_runs['Algorithm'] = df_runs.apply(extract_algo_name, axis=1)
    
    if 'metrics.rmse' in df_runs.columns:
        df_runs['metrics.rmse'] = pd.to_numeric(df_runs['metrics.rmse'], errors='coerce').fillna(0)
    
    if 'metrics.r2' in df_runs.columns:
        df_runs['metrics.r2'] = pd.to_numeric(df_runs['metrics.r2'], errors='coerce').fillna(0)
        df_runs['safe_size'] = df_runs['metrics.r2'].apply(lambda x: max(0.1, x) if x > 0 else 0.1)
    else:
        df_runs['metrics.r2'] = 0.0
        df_runs['safe_size'] = 0.1

    # KPI KARTLARI
    if 'metrics.rmse' in df_runs.columns:
        valid_runs = df_runs[df_runs['metrics.rmse'] > 0]
        if not valid_runs.empty:
            best_run = valid_runs.sort_values(by='metrics.rmse', ascending=True).iloc[0]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(" Şampiyon Model", best_run['Algorithm'], "Canlıda Aktif")
            with col2:
                st.metric(" En Düşük Hata (RMSE)", f"{best_run['metrics.rmse']:.2f} $", delta_color="inverse")
            with col3:
                st.metric(" En Yüksek Başarı (R2)", f"{best_run['metrics.r2']:.4f}")
            with col4:
                st.metric(" Toplam Model Eğitimi", len(df_runs))

    st.divider()

    # GRAFİK ALANI
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader(" Algoritma Kararlılık Analizi")
        fig_box = px.box(
            df_runs, 
            x="Algorithm", 
            y="metrics.rmse", 
            color="Algorithm",
            points="all",
            title="Hata Dağılımı (Box Plot)",
            template="plotly_dark",
            labels={"metrics.rmse": "Hata Payı (RMSE)", "Algorithm": "Algoritma"}
        )
        st.plotly_chart(fig_box, use_container_width=True)

    with c2:
        st.subheader(" Başarı vs Hata Analizi")
        fig_scatter = px.scatter(
            df_runs,
            x="metrics.rmse",
            y="metrics.r2",
            color="Algorithm",
            size="safe_size",
            hover_data=["start_time"],
            title="R2 Skoru vs RMSE İlişkisi",
            template="plotly_dark",
            labels={"metrics.rmse": "Hata (RMSE)", "metrics.r2": "Başarı (R2)"}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Grafik 3
    st.subheader("⏳ Zaman Serisi Performans Takibi")
    fig_line = px.line(
        df_runs, 
        x="start_time", 
        y="metrics.rmse", 
        color="Algorithm",
        markers=True,
        title="Model Hata Oranının Zamanla Değişimi",
        template="plotly_dark",
        labels={"start_time": "Eğitim Zamanı", "metrics.rmse": "Hata (RMSE)"}
    )
    st.plotly_chart(fig_line, use_container_width=True)

    #TABLO
    st.divider()
    st.subheader(" Detaylı Eğitim Kayıtları")
    
    cols = ['start_time', 'Algorithm', 'metrics.rmse', 'metrics.r2', 'run_id']
    cols = [c for c in cols if c in df_runs.columns]
    
    display_df = df_runs[cols].head(20).copy()
    display_df.columns = ["Zaman", "Algoritma", "Hata (RMSE)", "Başarı (R2)", "Run ID"]
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.warning(" Henüz analiz edilecek eğitim verisi bulunamadı.")
    st.info("Sistem veri topladıkça burası otomatik dolacaktır.")

#SIDEBAR
with st.sidebar:
    st.header(" Kontrol Paneli")
    if st.button(" Analizi Yenile", type="primary"):

        st.rerun()
