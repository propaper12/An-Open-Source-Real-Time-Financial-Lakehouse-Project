#!/bin/bash

# --- 1. GÖRSEL AYARLAR ---
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- 2. DOCKER KAYNAK SINIRLANDIRMA (CPU & RAM) ---
# Mac ve Linux'ta Docker kaynaklarını docker-compose üzerinden 
# veya Docker Desktop ayarlarından yönetmek en sağlıklısıdır.
# Ancak bu script, konteynerlerin toplamda sistemi yormamasını sağlar.

show_menu() {
    clear
    echo -e "${BLUE}#########################################################################${NC}"
    echo -e "${BLUE}#                                                                       #${NC}"
    echo -e "${BLUE}#                 F I N A N C I A L   L A K E H O U S E                 #${NC}"
    echo -e "${BLUE}#                 Unix/Mac DevOps Command Center                        #${NC}"
    echo -e "${BLUE}#                                                                       #${NC}"
    echo -e "${BLUE}#########################################################################${NC}"
    echo ""
    echo -e "  ${YELLOW}⚙️ ALTYAPI KONTROLU                 🔄 HOT RELOAD (GUNCELLEME)${NC}"
    echo -e "  [1] 🟢 Sistemi Baslat (Up)          [5] 🎨 Arayuz (Dashboard)"
    echo -e "  [2] 🔴 Sistemi Durdur (Stop)        [6] 🧠 AI Motoru (Silver)"
    echo -e "  [3] ⚠️  Sistemi Sifirla (Down -v)   [7] 📥 Veri Toplayici (Bronze)"
    echo -e "  [4] 🩺 Saglik Durumu (Health)       [8] 📡 Veri Uretici (Producer)"
    echo ""
    echo -e "  ${YELLOW}🤖 MLOps VE YAPAY ZEKA              🛠️ ARACLAR VE RAPORLAMA${NC}"
    echo -e "  [10] 🎯 Toplu Model Egitimi         [15] 📋 Canli Loglari Izle"
    echo -e "  [11] 🧪 Spesifik Coin Egitimi       [16] 🔗 Sistem Linkleri"
    echo -e "  [13] 🧹 Postgres Temizle            [17] 📊 Kaynak Izle (Stats)"
    echo -e "  [18] 🚪 Sistemden Cikis             [19] ⏳ Gecmis Veri Cek"
    echo ""
}

while true; do
    show_menu
    read -p "  [root@lakehouse]~# Komut Girin (1-19): " choice
    case $choice in
        1)
            echo -e "${GREEN}[ ⚙️ PROCESS ] Servisler ayaga kaldiriliyor...${NC}"
            docker-compose up -d
            read -p "Devam etmek icin Enter..."
            ;;
        2)
            echo -e "${RED}[ ⚙️ PROCESS ] Konteynerler durduruluyor...${NC}"
            docker-compose stop
            read -p "Devam etmek icin Enter..."
            ;;
        3)
            echo -e "${RED}⚠️  KRITIK UYARI: DB, Kafka ve MinIO SIFIRLANACAKTIR!${NC}"
            read -p "Onayliyor musunuz? (e/h): " confirm
            if [ "$confirm" == "e" ]; then
                docker-compose down -v
                echo -e "${GREEN}[ OK ] Sistem sifirlandi.${NC}"
            fi
            read -p "Devam etmek icin Enter..."
            ;;
        4)
            echo -e "${BLUE}[ 🩺 HEALTH ] Konteyner Durumu:${NC}"
            docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
            read -p "Devam etmek icin Enter..."
            ;;
        5)
            docker-compose up -d --build dashboard
            ;;
        6)
            docker-compose up -d --build spark-silver
            ;;
        9)
            docker-compose up -d --build dashboard spark-silver spark-consumer producer
            ;;
        10)
            echo -e "${GREEN}[ 🤖 MLOps ] AutoML Engine Baslatiliyor...${NC}"
            docker exec -it spark-silver python /app/train_model.py ALL
            read -p "Devam etmek icin Enter..."
            ;;
        13)
            echo -e "${GREEN}[ 🗄️ DataOps ] Postgres temizleniyor...${NC}"
            docker exec -it postgres psql -U admin_lakehouse -d market_db -c "TRUNCATE TABLE market_data;"
            read -p "Devam etmek icin Enter..."
            ;;
        15)
            echo "1) Dashboard  2) Silver  3) Bronze  4) Producer"
            read -p "Secim: " l_choice
            case $l_choice in
                1) docker logs -f dashboard ;;
                2) docker logs -f spark-silver ;;
                3) docker logs -f spark-consumer ;;
                4) docker logs -f producer ;;
            esac
            ;;
        17)
            docker stats
            ;;
        18)
            exit 0
            ;;
        *)
            echo -e "${RED}Gecersiz secim!${NC}"
            sleep 1
            ;;
    esac
done