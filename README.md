# yem_sistem

`yem_sistem`, yem merkezi için yerel envanter ve üretim kontrol sisteminin backend temelini oluşturan bir projedir.

## Ana Hedefler

- Mal kabul hareketlerini (IN) izlemek
- DTM üretim tüketim hareketlerini (OUT) izlemek
- Negatif stok oluşumunu engellemek
- Şüpheli batch yönetimi
- Aylık fiyatlandırma ve muhasebe export

## Modül Yapısı

```text
src/yem_sistem/
├── acceptance/
├── audit_logs/
├── batch_items/
├── db/
├── imports/
├── materials/
├── monthly_prices/
├── pen_daily/
├── production_batches/
├── stock_movements/
└── web/
```

## Acceptance Endpointleri

- `POST /acceptance`
- `GET /acceptance/new` (Bootstrap form)
- `GET /acceptance` (son 50 kayıt)

Rol kuralı: yalnızca `ACCEPTANCE` ve `ADMIN` rolleri acceptance insert yapabilir (`X-Role` header).

## Çalıştırma

```bash
uvicorn yem_sistem.web.app:app --reload
```
