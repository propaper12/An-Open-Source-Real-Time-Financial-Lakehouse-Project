
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select processed_time
from "market_db"."public"."crypto_prices"
where processed_time is null



  
  
      
    ) dbt_internal_test