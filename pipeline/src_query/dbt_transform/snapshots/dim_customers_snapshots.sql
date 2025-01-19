{% snapshot dim_customers_snapshot %}

{{
    config(
        target_database="pacbook-dwh",
        target_schema="final",
        unique_key="sk_customer_id",

        strategy="timestamp",
        updated_at="updated_at"
    )
}}

select *
from {{ ref("dim_customers") }} 

{% endsnapshot %}