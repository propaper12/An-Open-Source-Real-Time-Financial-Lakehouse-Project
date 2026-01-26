
  create view "market_db"."public"."stg_crypto_prices__dbt_tmp"
    
    
  as (
    

with raw_data as (
    select * from "market_db"."public"."crypto_prices"
)

select
    symbol,
    average_price as current_price, -- "price" yerine "average_price" yazdık
    predicted_price as ai_prediction,
    -- Hata payını hesapla
    abs(average_price - predicted_price) as prediction_error,
    processed_time as event_timestamp
from raw_data
  );