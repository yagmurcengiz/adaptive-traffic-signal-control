# Servisler Arası Sözleşme (Taslak v0.1)

Bu dosya, SUMO tarafı ile veri hattı tarafı arasındaki **tek gerçek kaynaktır**.
Alan adı veya tip değişecekse önce bu dosya güncellenir, sonra kod.

etiketli maddeler iki tarafın onayını bekliyor. Önerilen varsayılan değer yazılıdır.

## 1. Genel kurallar

- Tüm mesajlar **UTF-8 JSON**, tek satır, bir mesaj = bir kayıt.
- Zaman damgaları (`*_ts`): **Unix epoch, saniye, float** (ör. `1795675756.123`), gerçek duvar saati.
- `sim_time`: simülasyon saniyesi (float), SUMO'nun kendi saati.
- Birimler: hız **m/s**, bekleme **saniye**, kuyruk **araç sayısı**, doluluk **0-1 oranı**.
- Alan adları `snake_case`. Topic adları yalnızca nokta içerir (alt çizgi yok).
- Topic ve servis adları koda gömülmez, `.env` üzerinden okunur.
- Mesaj anahtarı (Kafka key): `tls_id`.

## 2. Topic listesi

| Topic | Üretici | Tüketici | `.env` değişkeni |
|---|---|---|---|
| `traffic.raw` | sumo_bridge | Spark | `TOPIC_RAW` |
| `traffic.metrics` | Spark | decision_service | `TOPIC_METRICS` |
| `control.commands` | decision_service | sumo_bridge, event_sink | `TOPIC_COMMANDS` |
| `control.applied` | sumo_bridge | event_sink | `TOPIC_APPLIED` (yeni) |
| `run.events` (opsiyonel) | sumo_bridge | experiments | `TOPIC_RUN_EVENTS` (yeni) |

`control.applied` ve `run.events` topic'leri eklensin mi? Önerim: evet.
Gerekçe: komutun uygulandığı an (`applied_ts`) yalnızca sumo_bridge'de bilinir.

## 3. `traffic.raw`

Üretici: sumo_bridge. **Her kavşağın her giriş şeridi için her örnekleme adımında bir mesaj.**

```json
{
  "run_id": "S2_adaptive_seed22",
  "scenario": "S2",
  "controller": "adaptive",
  "seed": 22,
  "sim_time": 345.0,
  "tls_id": "K1",
  "lane_id": "K1_n_0",
  "queue_length": 7,
  "waiting_time": 41.5,
  "mean_speed": 3.2,
  "occupancy": 0.41,
  "produced_ts": 1795675756.123
}
```

| Alan | Tip | Açıklama | TraCI karşılığı |
|---|---|---|---|
| `run_id` | string | `{senaryo}_{kontrol}_seed{N}` | bridge üretir |
| `scenario` | string | `S1`, `S2`, `S3` | config |
| `controller` | string | `fixed` veya `adaptive` | config |
| `seed` | int | rastgele tohum | config |
| `sim_time` | float | simülasyon saniyesi | `simulation.getTime()` |
| `tls_id` | string | `K1`, `K2`, `K3` (SUMO TLS id'lerinin eşlemesi config'de) | `trafficlight` |
| `lane_id` | string | giriş şeridi id'si | `lane` |
| `queue_length` | int | duran araç sayısı | `lane.getLastStepHaltingNumber` |
| `waiting_time` | float | şeritteki toplam bekleme (sn) | `lane.getWaitingTime` |
| `mean_speed` | float | ortalama hız (m/s) | `lane.getLastStepMeanSpeed` |
| `occupancy` | float | doluluk, 0-1 | `lane.getLastStepOccupancy` / 100 |
| `produced_ts` | float | mesajın üretildiği gerçek an | `time.time()` |

TraCI `getLastStepOccupancy` yüzde döndürür (0-100). Önerim: bridge 100'e bölüp 0-1 yollasın.
`waiting_time` şerit toplamı mı, araç başına ortalama mı? Önerim: şerit toplamı.
`lane_id` yerine `tls_id` bazında toplanmış tek mesaj mı? Önerim: şerit bazlı kalsın, toplama Spark'ta yapılır.

## 4. `traffic.metrics`

Üretici: Spark. Kavşak başına, pencere başına bir mesaj. Alanlar `traffic.traffic_metrics` tablosuyla birebir aynıdır.

```json
{
  "run_id": "S2_adaptive_seed22",
  "scenario": "S2",
  "controller": "adaptive",
  "seed": 22,
  "tls_id": "K1",
  "window_start": "2026-11-26T08:20:00.000Z",
  "window_end": "2026-11-26T08:20:10.000Z",
  "avg_queue": 6.4,
  "max_queue": 11.0,
  "avg_waiting": 38.2,
  "avg_speed": 3.9,
  "avg_occupancy": 0.37,
  "record_count": 20,
  "max_produced_ts": 1795675756.123
}
```

- `max_produced_ts`: pencerede görülen en son `produced_ts`. Karar servisi bunu `trigger_produced_ts` olarak kopyalar.
- Pencereler kayar olduğundan aynı `tls_id` için üst üste binen pencereler gelir. Karar servisi `window_end` ile sıralamalı, tekrarları dikkate almalıdır.

Karar servisi pencere kayması yüzünden her pencerede mi karar versin, yoksa yalnızca `window_end` sınırında mı? Önerim: her mesajda değerlendir, "ardışık pencere" sayacını `window_end` değişimine göre artır.

## 5. `control.commands`

Üretici: decision_service. Tüketici: sumo_bridge (uygular), event_sink (kaydeder).

```json
{
  "run_id": "S2_adaptive_seed22",
  "tls_id": "K1",
  "old_plan": "A",
  "new_plan": "B",
  "reason": "high_queue_3_windows",
  "trigger_produced_ts": 1795675756.123,
  "decision_ts": 1795675760.5
}
```

- Plan adları: `A` (sabit/baseline), `B` (ana yön uzun yeşil), `C` (yan yön uzun yeşil). SUMO'daki tlLogic `programID` değerleriyle **aynı** olmalı.
- Komut yalnızca plan **değişeceği** zaman gönderilir.

## 6. `control.applied`

Üretici: sumo_bridge. Komut `setProgram` ile uygulandıktan hemen sonra yazılır.

```json
{
  "run_id": "S2_adaptive_seed22",
  "tls_id": "K1",
  "new_plan": "B",
  "sim_time": 360.0,
  "applied_ts": 1795675760.9,
  "decision_ts": 1795675760.5
}
```

## 7. `run.events` (opsiyonel)

Koşu başında ve sonunda bir mesaj. Deney otomasyonu koşunun bittiğini buradan anlar.

```json
{"run_id": "S2_adaptive_seed22", "event": "start", "sim_time": 0.0, "event_ts": 1795675700.0}
{"run_id": "S2_adaptive_seed22", "event": "end",   "sim_time": 1800.0, "event_ts": 1795675990.0}
```

## 8. Gecikme zinciri

```
produced_ts ──► max_produced_ts ──► decision_ts ──► applied_ts
 (bridge)         (Spark)          (decision)       (bridge)
```

| Gecikme | Formül |
|---|---|
| Uçtan uca | `applied_ts - trigger_produced_ts` |
| Analiz + akış (Spark dahil) | `decision_ts - trigger_produced_ts` |
| Karar → uygulama | `applied_ts - decision_ts` |

Hesaplama `control_events` tablosunda yapılır (Grafana ve `analyze.py` kullanır).

## 9. Zamanlama parametreleri

| Parametre | Önerilen | Tutulduğu yer |
|---|---|---|
| Örnekleme aralığı | her 1 sim saniyesi | `.env` `SAMPLE_EVERY_STEPS` |
| Hız oranı (gerçek sn / sim sn) | 0.2 (yaklaşık 5 kat hızlı) | `.env` `SIM_PACE` |
| Spark pencere / kayma / watermark | 10 sn / 5 sn / 5 sn | `.env` `SPARK_*` |
| Karar servisi minimum kontrol aralığı | 30 sim sn | `config/thresholds.yaml` |
| Koşu süresi | 1800 sim sn | `config/scenarios.yaml` |

Spark pencereleri **gerçek zamana** göre işler. Simülasyon hızlandırılırsa pencere = daha çok sim saniyesi demektir. Hız oranı sabit tutulmalı ve raporda belirtilmeli.

## 10. Kimlikler ve adlandırma

- `run_id`: `{scenario}_{controller}_seed{seed}` (ör. `S1_fixed_seed11`).
- Seed'ler: `11, 22, 33`.
- `tls_id` eşlemesi: SUMO'daki gerçek TLS id'leri `config/scenarios.yaml` içinde `K1/K2/K3` etiketlerine eşlenir.

## 11. Fixed-time koşuları

`[TARTIŞILACAK]` Fixed koşusunda da bridge aynı mesajları `traffic.raw`'a yollar (Spark ve Grafana aynı akışla çalışsın), ancak decision_service çalışmaz ya da komut üretmez. Önerim: evet, `controller=fixed` etiketiyle.

## 12. Alınan kararlar

1. `control.applied` ve `run.events` topic'leri eklendi.
2. `occupancy` 0-1 aralığındadır, bridge 100'e bölüp gönderir.
3. `waiting_time` şerit toplamıdır.
4. Mesajlar şerit bazlıdır, kavşak toplamını Spark hesaplar.
5. `SIM_PACE` başlangıçta 0.2, ölçümle ayarlanacak.
6. Koşular sırayla çalışır.
7. Mesajlar düz JSON'dur.