# Gerçek Zamanlı Büyük Veri Tabanlı Adaptif Trafik Sinyal Kontrol Sistemi

Bu proje, gerçek bir kentsel yol ağı üzerinde SUMO simülasyonu, Apache Kafka, Apache Spark Structured Streaming, ClickHouse ve Grafana kullanarak eşik tabanlı adaptif trafik sinyal kontrolü gerçekleştiren modüler bir sistemdir.

## Sistem Mimarisi
- **Simülasyon:** OpenStreetMap + SUMO (TraCI)
- **Veri Akışı:** Python Producer -> Apache Kafka
- **Akış İşleme:** Spark Structured Streaming
- **Depolama & Görselleştirme:** ClickHouse + Grafana
- **Karar Döngüsü:** Bağımsız Karar Servisi (Eşik kontrolü + TraCI geri besleme)

## Gereksinimler
- Docker ve Docker Compose
- Git

## Kurulum ve Çalıştırma
*(Proje tamamlandığında tek komutla `docker compose up --build` adımları eklenecektir.)*