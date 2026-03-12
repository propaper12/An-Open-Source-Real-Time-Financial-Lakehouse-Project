import asyncio
import json
import os
import secrets
import redis.asyncio as aioredis
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request, WebSocket, Security, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from aiokafka import AIOKafkaConsumer
import asyncpg
from datetime import datetime
import bcrypt
import yfinance as yf
import copy
# ==============================================================================
# 🚀 RADAR GLOBAL - ENTERPRISE DATA GATEWAY (V11.6 SAAS EDITION)
# ==============================================================================
app = FastAPI(
    title="Radar Global - Data Gateway",
    description="Enterprise Grade Async API with Connection Pooling, Bcrypt & Full Settings.",
    version="11.6.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

KAFKA_SERVER = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = 'market_data'

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def hash_password(password: str):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# ==============================================================================
# 🏗️ LIFESPAN & CONNECTION POOL (BAĞLANTI HAVUZU)
# ==============================================================================
@app.on_event("startup")
async def startup_event():
    print("🟢 [RADAR] Asenkron Sistemler Ayağa Kalkıyor...")
    try:
        app.state.db_pool = await asyncpg.create_pool(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            database=os.getenv("POSTGRES_DB", "market_db"),
            user=os.getenv("POSTGRES_USER", "admin_lakehouse"),
            password=os.getenv("POSTGRES_PASSWORD", "SuperSecret_DB_Password_2026"),
            min_size=5,
            max_size=20 
        )
        print("🟢 [RADAR] PostgreSQL Connection Pool Aktif!")
    except Exception as e:
        print(f"🔴 [RADAR] DB Havuz Hatası: {e}")
        app.state.db_pool = None

    try:
        app.state.redis = await aioredis.from_url(f"redis://{os.getenv('REDIS_HOST', 'redis')}:6379", decode_responses=True)
        await app.state.redis.ping()
        print("🟢 [RADAR] Asenkron Redis Aktif!")
    except Exception as e:
        print(f"🔴 [RADAR] Redis Hatası: {e}")
        app.state.redis = None

    asyncio.create_task(consume_kafka_and_broadcast())

@app.on_event("shutdown")
async def shutdown_event():
    if getattr(app.state, "db_pool", None): await app.state.db_pool.close()
    if getattr(app.state, "redis", None): await app.state.redis.close()
    print("🔴 [RADAR] Sistem Güvenle Kapatıldı.")

# ==============================================================================
# 🛑 REDIS RATE LIMITING & SECURITY (ASYNC)
# ==============================================================================
async def check_redis_limit(email: str, tier: str):
    r = app.state.redis
    if r is None: return

    if await r.get(f"ban:{email}"):
        raise HTTPException(status_code=403, detail="⛔ HESABINIZ KALICI OLARAK BANLANDI! (Sistem Suistimali)")

    if tier == 'VIP':
        usage = await r.incr(f"rate:vip:{email}")
        if usage == 1: await r.expire(f"rate:vip:{email}", 1)
        if usage > 50: raise HTTPException(status_code=429, detail="🚨 VIP Sınırı: Saniyede 50 istek!")
        return 

    if tier == 'PREMIUM':
        usage = await r.incr(f"rate:premium:{email}")
        if usage == 1: await r.expire(f"rate:premium:{email}", 1)
        if usage > 10: raise HTTPException(status_code=429, detail="🚨 PREMIUM Sınırı: Saniyede 10 istek!")
        return

    if tier == 'FREE':
        today = datetime.now().strftime("%Y-%m-%d")
        limit_key = f"limit:free:{email}:{today}"
        usage = await r.incr(limit_key)
        if usage == 1: await r.expire(limit_key, 86400)
        
        if usage > 1000:
            await r.set(f"ban:{email}", "PERMANENT") 
            raise HTTPException(status_code=403, detail="⛔ GÜNLÜK 1000 İSTEK LİMİTİ AŞILDI. BANLANDINIZ.")

# ==============================================================================
# 🔐 AUTH MODELLERİ VE UÇ NOKTALAR (Kayıt, Giriş, Ayarlar)
# ==============================================================================
class UserRegister(BaseModel): 
    username: str
    email: str
    password: str

class UserLogin(BaseModel): 
    email: str
    password: str

class ProfileUpdate(BaseModel): 
    username: str

class PasswordChange(BaseModel): 
    current_password: str
    new_password: str

class TierUpdate(BaseModel): 
    email: str
    new_tier: str

@app.post("/api/v1/auth/register")
async def register_user(user: UserRegister, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    r = app.state.redis
    
    # GÜZELLEŞTİRME: Exception fırlatmak yerine frontend'e hatayı okutuyoruz
    if r:
        reg_count = await r.get(f"reg_ip:{client_ip}")
        if reg_count and int(reg_count) >= 3:
            return {"status": "error", "message": "🚨 Spam Koruması: Çok fazla hesap oluşturuldu. Lütfen bekleyin."}

    if not app.state.db_pool: 
        return {"status": "error", "message": "Sistem Hatası: Veritabanı bağlantısı kurulamadı."}
    
    try:
        async with app.state.db_pool.acquire() as conn:
            existing = await conn.fetchrow("SELECT username FROM api_users WHERE email = $1 OR username = $2", user.email, user.username)
            if existing: 
                return {"status": "error", "message": "E-posta veya kullanıcı adı zaten kullanımda!"}
            
            new_api_key = f"sk_live_{secrets.token_urlsafe(32)}"
            hashed_pw = hash_password(user.password)
            
            await conn.execute(
                "INSERT INTO api_users (username, email, api_key, tier, password_hash) VALUES ($1, $2, $3, $4, $5)",
                user.username, user.email, new_api_key, 'FREE', hashed_pw
            )

        if r:
            await r.incr(f"reg_ip:{client_ip}")
            await r.expire(f"reg_ip:{client_ip}", 3600) 

        return {"status": "success", "message": "Kayıt Başarılı!", "api_key": new_api_key}
    except Exception as e:
        return {"status": "error", "message": "Beklenmeyen bir veritabanı hatası oluştu."}

@app.post("/api/v1/auth/login")
async def login_user(user: UserLogin, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    r = app.state.redis
    
    if r:
        attempts = await r.get(f"bf_lock:{client_ip}")
        if attempts and int(attempts) >= 5:
            return {"status": "error", "message": "🚨 Güvenlik Kalkanı: Çok fazla hatalı giriş. 15 dakika engellendiniz."}

    if not app.state.db_pool: 
        return {"status": "error", "message": "Sistem Hatası: Veritabanı bağlantısı yok."}
    
    try:
        async with app.state.db_pool.acquire() as conn:
            record = await conn.fetchrow("SELECT username, email, api_key, tier, password_hash FROM api_users WHERE email = $1", user.email)
            
            if record and verify_password(user.password, record['password_hash']): 
                if r: await r.delete(f"bf_lock:{client_ip}") 
                return {"status": "success", "data": {"username": record['username'], "email": record['email'], "api_key": record['api_key'], "tier": record['tier']}}
            
            if r:
                await r.incr(f"bf_lock:{client_ip}")
                await r.expire(f"bf_lock:{client_ip}", 900) 
                
            return {"status": "error", "message": "E-posta adresi veya şifre hatalı!"}
    except Exception as e:
        return {"status": "error", "message": "Giriş işlemi sırasında sunucu hatası oluştu."}

@app.post("/api/v1/auth/admin_update_tier")
async def admin_update_tier(data: TierUpdate):
    if not app.state.db_pool: raise HTTPException(status_code=500, detail="DB Bağlantısı Yok.")
    async with app.state.db_pool.acquire() as conn:
        await conn.execute("UPDATE api_users SET tier = $1 WHERE email = $2", data.new_tier, data.email)
    return {"status": "success"}

# ==============================================================================
# 🔑 ZERO-TRUST SECURITY 
# ==============================================================================
async def verify_api_key(api_key_header: str = Security(api_key_header)):
    if not api_key_header: raise HTTPException(status_code=401, detail="API Anahtarı Eksik!")
    if not app.state.db_pool: raise HTTPException(status_code=500, detail="DB Bağlantısı Yok.")
    
    async with app.state.db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT username, email, tier FROM api_users WHERE api_key = $1", api_key_header)
    
    if not user: raise HTTPException(status_code=403, detail="Geçersiz API Anahtarı!")
    
    await check_redis_limit(user['email'], user['tier'])
    return dict(user)

# ==============================================================================
# 📊 YFINANCE PROXY - SADECE FREE TIER KULLANABİLİR
# ==============================================================================
@app.get("/api/v1/history/{symbol}")
async def get_historical_data(symbol: str, interval: str = "1h", period: str = "1d", user: dict = Security(verify_api_key)):
    if user['tier'] != 'FREE':
        raise HTTPException(
            status_code=403, 
            detail=f"Erişim Reddedildi! {user['tier']} kullanıcılar bu kanalı kullanamaz. Lütfen veritabanı uç noktalarını kullanın."
        )

    allowed_intervals = ["15m", "30m", "1h", "1d"]
    if interval not in allowed_intervals:
        raise HTTPException(status_code=400, detail=f"Desteklenen aralıklar: {allowed_intervals}")

    yf_symbol = symbol.replace("USDT", "-USD")
    try:
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty: raise HTTPException(status_code=404, detail="Veri bulunamadı.")
        
        df = df.reset_index()
        if 'Datetime' in df.columns: df['Date'] = df['Datetime']
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        data = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].to_dict(orient='records')
        
        return {
            "status": "success", 
            "tier": "FREE", 
            "source": "yfinance_proxy", 
            "interval": interval, 
            "data": data
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Harici veri çekme hatası.")

# ==============================================================================
# 📥 VERİ İNDİRME MERKEZİ - PREMIUM (12s) vs VIP (24s)
# ==============================================================================
@app.get("/api/v1/download/market")
async def download_market_data(user: dict = Security(verify_api_key)):
    tier = user['tier']
    
    if tier == 'FREE':
        raise HTTPException(status_code=403, detail="FREE paket sahipleri veritabanı dökümü alamaz.")

    # 🕒 PREMIUM 12 Saat, VIP 24 Saat sınırı
    time_limit = "12 hours" if tier == "PREMIUM" else "24 hours"
    
    async def iter_csv():
        yield "symbol,price,volume_usd,predicted_price,trade_side,processed_time\n"
        
        async with app.state.db_pool.acquire() as conn:
            async with conn.transaction():
                query = f"""
                    SELECT symbol, average_price, volume_usd, predicted_price, trade_side, processed_time 
                    FROM market_data 
                    WHERE processed_time >= NOW() - INTERVAL '{time_limit}' 
                    ORDER BY processed_time DESC
                """
                async for row in conn.cursor(query):
                    # 🔒 PREMIUM ise AI verilerini (Tahmin ve Yön) gizliyoruz
                    p_val = "HIDDEN" if tier == "PREMIUM" else row['predicted_price']
                    s_val = "HIDDEN" if tier == "PREMIUM" else row['trade_side']
                    
                    yield f"{row['symbol']},{row['average_price']},{row['volume_usd']},{p_val},{s_val},{row['processed_time']}\n"

    return StreamingResponse(
        iter_csv(), 
        media_type="text/csv", 
        headers={"Content-Disposition": f"attachment; filename=radar_extract_{tier.lower()}.csv"}
    )

# ==============================================================================
# 📊 ANLIK VERİ - FREE GİREMEZ, PREMIUM'DAN AI VERİLERİ SİLİNİR
# ==============================================================================
@app.get("/api/v1/market/{symbol}")
async def get_market_data(symbol: str, user: dict = Security(verify_api_key)):
    tier = user['tier']
    
    if tier == 'FREE':
        raise HTTPException(status_code=403, detail="Erişim Reddedildi! FREE paket sahipleri /history kullanmalıdır.")
    
    async with app.state.db_pool.acquire() as conn:
        record = await conn.fetchrow("SELECT * FROM market_data WHERE symbol = $1 ORDER BY processed_time DESC LIMIT 1;", symbol.upper())
        if not record: raise HTTPException(status_code=404, detail="Veri Bulunamadı.")
        
        record_dict = dict(record)
        
        # PREMIUM ise AI kolonlarını temizle
        if tier == 'PREMIUM':
            for key in ['predicted_price', 'is_buyer_maker', 'trade_side', 'cvd']:
                record_dict.pop(key, None)
            return {"status": "success", "tier": "PREMIUM", "data": record_dict}

        return {"status": "success", "tier": "VIP", "data": record_dict}


# ==============================================================================
# 🚀 ENTERPRISE PUB/SUB WEBSOCKET (SADECE VIP VE PREMIUM)
# ==============================================================================

class ConnectionManager:
    def __init__(self):
        # { "BTCUSDT": [ (ws, tier), ... ] }
        self.active_connections: dict[str, list[tuple[WebSocket, str]]] = {}

    async def connect(self, websocket: WebSocket, symbol: str, tier: str):
        await websocket.accept()
        if symbol not in self.active_connections:
            self.active_connections[symbol] = []
        self.active_connections[symbol].append((websocket, tier))

    def disconnect(self, websocket: WebSocket, symbol: str):
        if symbol in self.active_connections:
            self.active_connections[symbol] = [
                conn for conn in self.active_connections[symbol] if conn[0] != websocket
            ]

    async def broadcast(self, symbol: str, message: dict):
        if symbol in self.active_connections:
            for websocket, tier in self.active_connections[symbol]:
                try:
                    if tier == 'PREMIUM':
                        # Verinin kopyasını alıyoruz (VIP'ninkini bozmamak için)
                        import copy
                        payload = copy.deepcopy(message)
                        
                        # VIP'ye özel olan tüm 'yasaklı' alanları siliyoruz
                        # Hem 'data' içinde hem de ana objede arıyoruz
                        restricted = ['predicted_price', 'trade_side', 'cvd', 'is_buyer_maker']
                        
                        if 'data' in payload:
                            for key in restricted:
                                payload['data'].pop(key, None) # Varsa siler, yoksa hata vermez
                        
                        await websocket.send_json(payload)
                    else:
                        # 💎 VIP her şeyi olduğu gibi alır
                        await websocket.send_json(message)
                except Exception as e:
                    print(f"🔴 Yayın Hatası: {e}")
                    self.disconnect(websocket, symbol)

manager = ConnectionManager()

# TEK BİR WEBSOCKET ENDPOINT BIRAK:
@app.websocket("/api/v1/stream/{symbol}")
async def stream_live_data(websocket: WebSocket, symbol: str, api_key: str = Query(None)):
    if not api_key: return await websocket.close(code=1008)
    
    async with app.state.db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT tier FROM api_users WHERE api_key = $1", api_key)
        
        # Sadece PREMIUM ve VIP girebilir
        if not user or user['tier'] not in ['PREMIUM', 'VIP']:
            await websocket.accept()
            await websocket.send_json({"error": "ERİŞİM REDDEDİLDİ!"})
            return await websocket.close(code=1008)

        symbol_upper = symbol.upper()
        await manager.connect(websocket, symbol_upper, user['tier'])
        
    try:
        while True: await websocket.receive_text()
    except Exception: manager.disconnect(websocket, symbol_upper)

async def consume_kafka_and_broadcast():
    while True:
        try:
            consumer = AIOKafkaConsumer(
                KAFKA_TOPIC, 
                bootstrap_servers=KAFKA_SERVER, 
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            await consumer.start()
            async for msg in consumer:
                # Gelen veriyi 'data' anahtarı içine hapsediyoruz ki filtreleme kolaylaşsın
                full_payload = {"type": "LIVE_STREAM", "data": msg.value}
                symbol = msg.value.get("symbol", "").upper()
                
                if symbol in manager.active_connections:
                    await manager.broadcast(symbol, full_payload)
        except Exception as e:
            print(f"🔴 Kafka Consumer Hatası: {e}")
            await asyncio.sleep(3)
        finally:
            await consumer.stop()
