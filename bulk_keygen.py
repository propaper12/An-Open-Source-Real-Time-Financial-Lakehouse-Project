import secrets
import psycopg2

def generate_bulk_keys(count=20):
    print(f"🚀 {count} Adet VIP Müşteri Hesabı Oluşturuluyor...\n")
    
    # Veritabanına Bağlan (Docker dışından çalıştırdığımız için localhost)
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="market_db",
            user="admin_lakehouse",
            password="SuperSecret_DB_Password_2026"
        )
        cur = conn.cursor()
    except Exception as e:
        print(f"❌ Veritabanına bağlanılamadı: {e}")
        return

    # Müşterileri Oluştur ve Veritabanına Bas
    created_users = []
    for i in range(1, count + 1):
        username = f"VIP_Musteri_{i}"
        api_key = f"sk_live_{secrets.token_urlsafe(32)}"
        
        try:
            cur.execute(
                "INSERT INTO api_users (username, api_key, tier) VALUES (%s, %s, %s)",
                (username, api_key, 'VIP')
            )
            created_users.append({"user": username, "key": api_key})
        except Exception as e:
            print(f"Hata ({username}): {e}")

    # Değişiklikleri Kaydet
    conn.commit()
    cur.close()
    conn.close()

    # Sonuçları Ekrana Yazdır
    print(f"✅ Başarıyla {len(created_users)} müşteri oluşturuldu!\n")
    print("-" * 60)
    for u in created_users:
        print(f"👤 {u['user']} | 🔑 {u['key']}")
    print("-" * 60)

# 20 kişi için çalıştır
if __name__ == "__main__":
    generate_bulk_keys(20)