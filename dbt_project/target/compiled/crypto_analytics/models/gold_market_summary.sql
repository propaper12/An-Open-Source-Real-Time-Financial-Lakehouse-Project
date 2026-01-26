

SELECT
    symbol,
    DATE_TRUNC('minute', processed_time::TIMESTAMP) as zaman_dilimi,

    AVG(average_price) as ortalama_fiyat,
    MAX(average_price) as en_yuksek_fiyat,
    MIN(average_price) as en_dusuk_fiyat,

    COUNT(*) as islem_sayisi
FROM public.crypto_prices
GROUP BY 1, 2
ORDER BY 2 DESC