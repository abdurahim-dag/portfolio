with files as (
    select f.response_code_file_id,
           to_date(extract(year from response_code_file_date)::text || '.' || substring(response_code_file_name, '\d\d\.\d\d'), 'YYYY.DD.MM') as date_in
    from gko.response_code_file f
    where f.response_code_file_response_id is null
),
     files_resp as (
         select files.response_code_file_id, r.response_id
         from files
                  left join gko.request rq on rq.request_date = files.date_in
                  join gko.response r on r.response_request_id = rq.request_id
     )

update gko.response_code_file rcf
set  response_code_file_response_id = files_resp.response_id
from files_resp
where rcf.response_code_file_id=files_resp.response_code_file_id and rcf.response_code_file_response_id is null;