import streamlit as st
import pandas as pd
import mlflow
import plotly.express as px
from utils import inject_custom_css, init_mlflow

# Bu sayfayi tasarlarken amacim, kullanicinin MLflow'un o karmasik ekranina
# girmeden sadece "Hangi coin'de kim kazanmis" bilgisini gormesini saglamak.
st.set_page_config(page_title="AutoML Merkez Komutasi", layout="wide", page_icon="🗂️")
inject_custom_css()

is_connected, active_uri = init_mlflow()

c1, c2 = st.columns([3, 1])
with c1:
    st.title("🗂️ MLOps Model Klasorleri")
    st.caption("Her varlik icin egitilen modelleri kendi klasorunde inceleyin.")
with c2:
    if is_connected:
        st.success(f"MLflow Aktif: {active_uri}")
    else:
        st.error("MLflow Baglantisi Yok")

if is_connected:
    try:
        runs = mlflow.search_runs(search_all_experiments=True)
    except:
        runs = pd.DataFrame()

    if not runs.empty:
        # ==========================================
        # VERI AYRISTIRMA (PARENT - CHILD MANTIGI)
        # MLflow verisi normalde dumduz bir tablo olarak gelir. 
        # Ben burada Parent ID'ye bakarak "Ana Coin" ile "Egitilen Modeli" birbirinden ayirdim.
        # ==========================================
        parent_runs = runs[runs['tags.mlflow.parentRunId'].isna()].copy()
        child_runs = runs[runs['tags.mlflow.parentRunId'].notna()].copy()

        parent_symbol_map = parent_runs.set_index('run_id')['params.symbol'].to_dict()
        child_runs['Coin_Folder'] = child_runs['tags.mlflow.parentRunId'].map(parent_symbol_map)
        
        child_runs['RMSE'] = pd.to_numeric(child_runs['metrics.rmse'], errors='coerce').fillna(9999.0)
        
        if 'end_time' in child_runs.columns and 'start_time' in child_runs.columns:
            child_runs['Sure_ms'] = (pd.to_datetime(child_runs['end_time']) - pd.to_datetime(child_runs['start_time'])).dt.total_seconds() * 1000
        else:
            child_runs['Sure_ms'] = 100.0

        child_runs['Model_Name'] = child_runs['tags.mlflow.runName'].str.replace('_', ' ').str.upper()
        child_runs = child_runs.dropna(subset=['Coin_Folder']) 
        
        # UI/UX icin bilgileri iki sekmeye (Tab) boldum. 
        # Hepsi tek ekranda olsaydi cok karmasik ve yorucu olurdu.
        tab1, tab2 = st.tabs(["📂 Varlik Klasorleri", "🏆 Genel Sampiyonlar"])

        # ------------------------------------------
        # SEKME 1: KLASOR (COIN) BAZLI INCELEME
        # ------------------------------------------
        with tab1:
            st.markdown("### 🔍 Model Klasorune Gir")
            
            coin_list = sorted(child_runs['Coin_Folder'].unique())
            
            col_sel, col_empty = st.columns([1, 2])
            with col_sel:
                selected_folder = st.selectbox("Incelemek Istediginiz Varligi Secin:", coin_list)
            
            st.divider()
            
            # Sadece kullanicinin sectigi coine (ornegin BTCUSDT) ait modelleri listeliyorum
            folder_data = child_runs[child_runs['Coin_Folder'] == selected_folder].sort_values(by='RMSE').reset_index(drop=True)
            
            if not folder_data.empty:
                winner = folder_data.iloc[0]
                
                st.success(f"🥇 **{selected_folder}** icin Production'da calisan algoritma: **{winner['Model_Name']}**")
                
                c_m1, c_m2, c_m3 = st.columns(3)
                c_m1.metric("Sampiyonun Hata Payi (RMSE)", f"{winner['RMSE']:.5f}")
                c_m2.metric("Egitim Suresi", f"{winner['Sure_ms']:.0f} ms")
                c_m3.metric("Test Edilen Model Sayisi", len(folder_data))
                
                col_chart, col_table = st.columns([1.5, 1])
                
                with col_chart:
                    st.markdown(f"#### 📊 Algoritma Performanslari")
                    # Gorsellestirme icin Plotly tercih ettim cunku interaktif ve responsive.
                    fig_bar = px.bar(
                        folder_data, 
                        x='Model_Name', 
                        y='RMSE', 
                        color='RMSE',
                        text_auto='.5f',
                        color_continuous_scale='RdYlGn_r', 
                        template='plotly_dark'
                    )
                    fig_bar.update_layout(xaxis_title="Algoritma", yaxis_title="Hata Payi (Dusuk daha iyi)", coloraxis_showscale=False)
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                with col_table:
                    st.markdown("#### 📋 Egitim Kayitlari")
                    folder_display = folder_data[['Model_Name', 'RMSE', 'Sure_ms']].copy()
                    folder_display.index = folder_display.index + 1
                    
                    st.dataframe(
                        folder_display,
                        column_config={
                            "Model_Name": "Algoritma",
                            "RMSE": st.column_config.NumberColumn("RMSE", format="%.5f"),
                            "Sure_ms": st.column_config.NumberColumn("Sure", format="%d ms"),
                        },
                        use_container_width=True
                    )

        # ------------------------------------------
        # SEKME 2: TUM PIYASA GOZLEMI (GENEL)
        # ------------------------------------------
        with tab2:
            st.markdown("### 🏆 Tum Varliklarin Kazananlari")
            # Sadece her klasorun 1.sini filtreleyip aliyorum
            best_models = child_runs.loc[child_runs.groupby('Coin_Folder')['RMSE'].idxmin()].sort_values(by='RMSE').reset_index(drop=True)
            
            fig_scatter = px.scatter(
                best_models, x="Sure_ms", y="RMSE", color="Coin_Folder", size_max=60, hover_name="Model_Name", template="plotly_dark"
            )
            fig_scatter.update_layout(xaxis_title="Hiz (Egitim Suresi)", yaxis_title="Basari (Hata Payi)")
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            st.dataframe(
                best_models[['Coin_Folder', 'Model_Name', 'RMSE', 'Sure_ms']],
                column_config={
                    "Coin_Folder": "Varlik",
                    "Model_Name": "Sampiyon",
                    "RMSE": st.column_config.NumberColumn("Hata (RMSE)", format="%.5f"),
                    "Sure_ms": st.column_config.NumberColumn("Sure", format="%d ms")
                },
                use_container_width=True, hide_index=True
            )

    else:
        st.warning("Egitilmis model yok. Once egitimi baslatin.")