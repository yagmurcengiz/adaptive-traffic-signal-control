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
2. `copy .env.example .env` (Mac/Linux: `cp .env.example .env`)
3. `docker compose up -d --build`
4. İlk çalıştırmada Spark Kafka paketini indirir, birkaç dakika sürebilir.
5. Grafana: http://localhost:3000 (kullanıcı ve parola `.env` dosyasında)

## Servisler
| Servis | Görev | Port |
|---|---|---|
| kafka | olay akışı | 29092 |
| spark | pencere tabanlı analiz | - |
| clickhouse | zaman serisi depolama | 8123 |
| grafana | dashboard | 3000 |

## Yerel Betikler
python -m venv .venv, aktif et, `pip install -r experiments/requirements.txt`

## Deneyleri Çalıştırma
(sonra doldurulacak)

## Sorun Giderme
- "Cannot connect to the Docker daemon": Docker Desktop kapalı
- Spark sürekli yeniden başlıyor: `docker compose logs spark --tail 80`
- Parola değiştirdim ama eski parola geçerli: `docker compose down -v` ile veriyi sıfırla

## Kullanılan Üçüncü Taraf Yazılımlar
Kafka, Spark, ClickHouse, Grafana, SUMO, OpenStreetMap, ...   
