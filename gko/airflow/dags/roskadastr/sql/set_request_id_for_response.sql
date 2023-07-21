with req as (
    select request_date, request_id
    from gko.request
    where request_date>'2023-01-01'
),
     res as (
         select to_date(extract(year from response_date)::text || '.' || substring(response_name, '\d\d\.\d\d'), 'YYYY.DD.MM') as date_in,
                response_id
         from gko.response
         where response_request_id is null and response_date>'2023-01-24'
     ),
     res_req as (select res.response_id, req.request_id
                 from res
                          left join req on res.date_in=req.request_date)

update gko.response r set
    response_request_id=res_req.request_id
from res_req
where r.response_id=res_req.response_id;