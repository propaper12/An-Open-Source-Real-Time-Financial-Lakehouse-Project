{{ config(materialized='table') }}

select
    symbol,
    date_trunc('hour', event_timestamp) as observation_hour,
    avg(current_price) as avg_actual_price,
    avg(ai_prediction) as avg_predicted_price,
    -- Parantezleri kaldır, sadece sade bir isim ver veya alt çizgi kullan
    avg(prediction_error) as mean_absolute_error, 
    count(*) as tick_count
from {{ ref('stg_crypto_prices') }}
group by 1, 2
order by 2 desc