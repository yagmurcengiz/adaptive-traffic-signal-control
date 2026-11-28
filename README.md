# Gerçek Zamanlı Büyük Veri Tabanlı Adaptif Trafik Sinyal Kontrol Sistemi

Bu proje, gerçek bir kentsel yol ağı üzerinde SUMO simülasyonu, Apache Kafka, Apache Spark Structured Streaming, ClickHouse ve Grafana kullanarak eşik tabanlı adaptif trafik sinyal kontrolü gerçekleştiren modüler bir sistemdir.

## Sistem Mimarisi
- **Simülasyon:** OpenStreetMap + SUMO (TraCI)
- **Veri Akışı:** Python Producer -> Apache Kafka
- **Akış İşleme:** Spark Structured Streaming
- **Depolama & Görselleştirme:** ClickHouse + Grafana
- **Karar Döngüsü:** Bağımsız Karar Servisi (Eşik kontrolü + TraCI geri besleme)

## Gereksinimler
- Docker Desktop (WSL2)
- Git
- Python 3.10+

## Kurulum ve Çalıştırma
1. `git clone <repo-adresi>` ve klasöre gir
2. Ayar dosyasını oluşturun:
   - Windows: `copy .env.example .env`
   - Mac/Linux: `cp .env.example .env`
3. İsterseniz `.env` içindeki `change_me` parolalarını değiştirin.
4. Tüm servisleri başlatın:
```
docker compose up -d --build
```
5. Durumu kontrol edin:
```
docker compose ps -a
```
   `kafka-init` için `Exited (0)` görmeniz normaldir (topic'leri oluşturup kapanır). Diğer servisler `Up` olmalıdır.
 
İlk çalıştırmada Spark, Kafka bağlantı paketini internetten indirir. Bu birkaç dakika sürebilir.
## Servisler
| Servis | Görev | Adres |
|---|---|---|
| `kafka` | Olay akışı | `localhost:29092` (konteynerler arası `kafka:9092`) |
| `kafka-init` | Topic'leri oluşturur | - |
| `spark` | Pencere tabanlı akış analizi | - |
| `clickhouse` | Zaman serisi depolama | `http://localhost:8123` |
| `grafana` | Dashboard | `http://localhost:3000` |
 
Grafana kullanıcı adı ve parolası `.env` dosyasındaki `GRAFANA_ADMIN_USER` ve `GRAFANA_ADMIN_PASSWORD` değerleridir. Veri kaynağı ve `Traffic Control` dashboard'u otomatik yüklenir, elle ayar gerekmez.

## Yerel Betikler
python -m venv .venv, aktif et, `pip install -r experiments/requirements.txt`

## Deneyleri Çalıştırma
(sonra doldurulacak)

## Sahte veriyle deneme
 
SUMO tarafı hazır olmadan hattı denemek için iki sahte üretici vardır. Yerel betikler için sanal ortam kurun:
 
```
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r experiments/requirements.txt
```
 
Ayrı iki terminalde (sanal ortam aktifken, depo ana klasöründen):
 
```
python experiments/fake_producer.py
python experiments/fake_controller.py
```
 
Yaklaşık bir dakika sonra Grafana'da `Traffic Control` dashboard'unu açıp `run_id` olarak `fake_run` seçin. Paneller dolmalıdır.
 
## Deneyleri çalıştırma ve analiz
 
Bir koşu bittikten sonra özetini `run_summary` tablosuna yazmak için:
 
```
python experiments/summarize_run.py RUN_ID --tripinfo yol/tripinfo.xml
```
 
Tüm koşular özetlendikten sonra karşılaştırma tablosu ve grafikleri üretmek için:
 
```
python experiments/analyze.py
```
 
Çıktılar `experiments/results/` klasörüne yazılır (ortalama ve standart sapma tablosu, yüzde iyileşme tablosu, metrik başına grafik).
 
Koşu adı biçimi: `{senaryo}_{kontrol}_seed{N}` (örn. `S2_adaptive_seed22`).
 
## Klasör yapısı
 
```
.
├── docker-compose.yml        # tüm servisler
├── .env.example              # ayar şablonu
├── config/                   # eşik ve senaryo ayarları
├── sumo/                     # harita, ışık planları, rota dosyaları
├── services/
│   ├── spark_streaming/      # Spark akış işi
│   ├── sumo_bridge/          # SUMO + TraCI + Kafka köprüsü
│   └── decision_service/     # eşik tabanlı karar servisi
├── infra/
│   ├── clickhouse/init.sql   # tablo şemaları
│   └── grafana/              # veri kaynağı ve dashboard tanımları
├── experiments/              # deney ve analiz betikleri
└── docs/                     # mesaj sözleşmeleri, mimari şema
```
 
## Sık karşılaşılan sorunlar
 
| Sorun | Çözüm |
|---|---|
| `Cannot connect to the Docker daemon` | Docker Desktop açık değil, açıp "Engine running" yazmasını bekleyin |
| `port is already allocated` | Port başka bir programda kullanımda, `.env` içinde portu değiştirin |
| Parolayı değiştirdim ama eski parola geçerli | ClickHouse ve Grafana parolayı yalnızca ilk açılışta kaydeder. `docker compose down -v` ile verileri sıfırlayıp yeniden başlatın |
| Spark sürekli yeniden başlıyor | `docker compose logs spark --tail 80` çıktısındaki ilk hata satırına bakın. Çoğunlukla `.env` içinde eksik değişkendir |
| `.env` değişikliği işe yaramıyor | `docker compose up -d --force-recreate` ile servisleri yeniden oluşturun |
| Grafana'da dashboard görünmüyor | `docker compose logs grafana --tail 30` içinde `failed to save dashboard` arayın |
| Paneller "No data" gösteriyor | `run_id` listesinde bir koşu seçili mi, üreticiler çalışıyor mu, zaman aralığı güncel mi kontrol edin |
| Spark çıktısı gecikmeli geliyor | Pencereler watermark geçince yazılır, birkaç on saniye gecikme normaldir |
 
## Veri sıfırlama
 
Tüm veriyi (Kafka topic'leri, ClickHouse tabloları, Grafana ayarları) silip temiz başlamak için:
 
```
docker compose down -v
docker compose up -d --build
```
