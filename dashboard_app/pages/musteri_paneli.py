import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="RadarPro | Veri Terminali", layout="wide", page_icon="📡")

API_BASE_URL = "http://api-gateway:8000/api/v1"
# Streamlit Docker dışındaysa http://localhost:8000/api/v1 kullanmalısın, Docker içindeyse api-gateway kalsın.
# Eğer API'ye bağlanmazsa yukarıyı http://localhost:8000/api/v1 olarak değiştir!

COINS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "AVAXUSDT", 
    "DOGEUSDT", "DOTUSDT", "MATICUSDT", "LINKUSDT", "UNIUSDT", "LTCUSDT"
]

if "api_key" not in st.session_state: st.session_state["api_key"] = None
if "tier" not in st.session_state: st.session_state["tier"] = None
if "email" not in st.session_state: st.session_state["email"] = None

# ==============================================================================
# 🔐 GİRİŞ EKRANI
# ==============================================================================
def auth_screen():
    st.markdown("<h1 style='text-align: center;'>Radar<span style='color:#2962FF'>Pro</span> DaaS Terminal</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        log_email = st.text_input("E-posta Adresi", placeholder="ornek@radar.com")
        log_pass = st.text_input("Şifre", type="password")
        if st.button("Sisteme Gir", use_container_width=True):
            try:
                res = requests.post(f"{API_BASE_URL}/auth/login", json={"email": log_email, "password": log_pass})
                if res.status_code == 200 and res.json().get("status") == "success":
                    data = res.json()["data"]
                    st.session_state.update({"api_key": data["api_key"], "tier": data["tier"], "email": data["email"]})
                    st.rerun()
                else: st.error("Giriş Başarısız.")
            except Exception as e:
                st.error("Bağlantı Hatası. API çalışıyor mu?")

# ==============================================================================
# 📊 ANA TERMİNAL
# ==============================================================================
def main_dashboard():
    # --- YAN PANEL ---
    with st.sidebar:
        st.markdown("### 🛠️ Geliştirici Paneli")
        st.caption(f"Kullanıcı: {st.session_state['email']}")
        
        new_tier = st.radio("Yetki Değiştir (Test):", ["FREE", "PRO", "VIP"], index=["FREE", "PRO", "VIP"].index(st.session_state['tier']))
        if st.button("Yetkiyi Güncelle"):
            requests.post(f"{API_BASE_URL}/auth/admin_update_tier", json={"email": st.session_state['email'], "new_tier": new_tier})
            st.session_state['tier'] = new_tier
            st.success(f"Yetki {new_tier} yapıldı!")
            time.sleep(1)
            st.rerun()
            
        st.markdown("---")
        st.markdown("### 📥 Veri İndirme Merkezi")
        
        # 🚀 YENİ: TIER'A GÖRE İNDİRME BUTONLARI
        if st.session_state['tier'] == "FREE":
            st.info("💡 FREE kullanıcılar harici kaynaklardan (Yahoo Finance) gecikmeli geçmiş verileri indirebilir.")
            if st.button("📈 1 Aylık Geçmişi İndir (YFinance)"):
                with st.spinner("Harici kaynaktan çekiliyor..."):
                    h_res = requests.get(f"{API_BASE_URL}/history/BTCUSDT", headers={"X-API-Key": st.session_state['api_key']})
                    if h_res.status_code == 200:
                        df_history = pd.DataFrame(h_res.json()['data'])
                        csv = df_history.to_csv(index=False).encode('utf-8')
                        st.download_button(label="📥 CSV'yi Kaydet", data=csv, file_name="yfinance_free_data.csv", mime="text/csv")
                    else:
                        st.error("Veri çekilemedi.")
        else:
            st.success(f"⚡ {st.session_state['tier']} Paket: Veritabanından yüksek hızlı ham veri indirme aktif.")
            st.markdown(f"Son {'6 Saat' if st.session_state['tier'] == 'PRO' else '24 Saat'} - Saniyelik Veri")
            st.markdown("[📥 Ana Veritabanından İndir (API Endpoint)](http://localhost:8000/api/v1/download/market)")
        
        st.markdown("---")
        if st.button("🚪 Çıkış Yap"):
            st.session_state.clear()
            st.rerun()

    # --- ANA EKRAN ---
    st.title("📡 Canlı Veri Akışı")
    symbol = st.selectbox("Görüntülenecek Sembol:", COINS, index=0)
    st.markdown("---")
    placeholder = st.empty()

    while True:
        try:
            headers = {"X-API-Key": st.session_state["api_key"]}
            res = requests.get(f"{API_BASE_URL}/market/{symbol}", headers=headers)
            
            if res.status_code == 200:
                payload = res.json()
                veri = payload["data"]
                tier_info = payload["tier"]
                
                with placeholder.container():
                    if tier_info == "FREE": 
                        st.error(f"⏳ **FREE Paket:** Veriler 1 dakika gecikmelidir. Ana veritabanına erişim kısıtlıdır.")
                        
                        st.markdown("### 📊 1 Dk Gecikmeli Fiyat & Günlük Özet")
                        c1, c2, c3, c4 = st.columns(4)
                        # "or 0" ile None (Null) hatalarını engelliyoruz
                        c1.metric("Gecikmeli Fiyat", f"${veri.get('delayed_price') or 0:,.2f}")
                        c2.metric("24s Ortalama", f"${veri.get('avg_p') or 0:,.2f}")
                        c3.metric("24s Zirve", f"${veri.get('max_p') or 0:,.2f}")
                        c4.metric("24s Dip", f"${veri.get('min_p') or 0:,.2f}")
                        st.caption(f"Veritabanı Zaman Damgası: {veri.get('processed_time', '')}")
                        
                    else:
                        st.success(f"💎 **{tier_info} Paket:** Gerçek zamanlı veri akışı devrede.")
                        st.markdown("### ⚡ Anlık Piyasa Verileri")
                        col1, col2, col3 = st.columns(3)
                        col1.metric(f"Mevcut Fiyat ({symbol})", f"${veri.get('average_price') or 0:,.2f}")
                        col2.metric("İşlem Hacmi (USD)", f"${veri.get('volume_usd') or 0:,.0f}")
                        col3.metric("Veri Zamanı", veri.get('processed_time', '')[11:19])

                        st.markdown("### 🧠 AI Model & Derin Analiz")
                        pc1, pc2, pc3 = st.columns(3)
                        
                        if tier_info == "VIP":
                            fark = (veri.get('predicted_price') or 0) - (veri.get('average_price') or 0)
                            pc1.metric("Yapay Zeka Fiyat Tahmini", f"${veri.get('predicted_price') or 0:,.2f}", delta=f"{fark:,.2f} USD")
                            pc2.metric("CVD (Alım/Satım Baskısı)", f"{veri.get('cvd') or 0:,.2f}")
                            pc3.metric("Yön Sinyali", str(veri.get('trade_side', 'N/A')))
                        else:
                            pc1.metric("Yapay Zeka Tahmini", "🔒 VIP'ye Özel")
                            pc2.metric("CVD (Baskı Endeksi)", "🔒 VIP'ye Özel")
                            pc3.metric("Sinyal Yönü", "🔒 VIP'ye Özel")

            elif res.status_code == 404:
                with placeholder.container(): st.warning(f"⚠️ '{symbol}' için veri bekleniyor... (Sistemde henüz 1 dakikalık veri birikmemiş olabilir, lütfen 30 saniye bekleyin.)")
            else:
                pass
                
        except Exception as e:
            pass
            
        time.sleep(2)

if st.session_state["api_key"]: main_dashboard()
else: auth_screen()