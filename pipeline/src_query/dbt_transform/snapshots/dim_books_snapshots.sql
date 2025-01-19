{% snapshot dim_books_snapshot %}

{{
    config(
        target_database="pacbook-dwh",
        target_schema="final",
        unique_key="sk_book_id",

        strategy="timestamp",
        updated_at="updated_at"
    )
}}

select *
from {{ ref("dim_books") }} 

{% endsnapshot %}