insert into gko.request(request_date, request_reg_num, request_type_id, request_name, request_description, request_pdf)
select distinct on (r.date, r.name) r.date, '' as reg_num, 0 as type_id, r.name, r.description, rp.pdf
from reestrin r
         left join reestrin_pdf rp on r."name" = rp."name" and r."date" = rp."date";

insert into gko.request_file(request_file_name, request_file_path, request_id, request_file_content, request_file_options)
select x.file_name, r.description, gr.request_id, x.xlss, jsonb_build_object('value', r.options)
from public.xlss x
         left join public.reestrin r on r.id=x.reestrin_id
         join gko.request gr on gr.request_date = r.date and gr.request_name = r.name;

insert into gko.request_file(request_file_name, request_file_path, request_id, request_file_content, request_file_options)
select x.file_name, r.description, gr.request_id, x.xml,  r.options
from public.xmls x
         left join public.reestrin r on r.id=x.reestrin_id
         join gko.request gr on gr.request_date = r.date and gr.request_name = r.name;


insert into gko.response(response_name, response_date, response_type_id, response_pdf)
select distinct on (m.name, m.date_in) m.name, m.date_in, 0 as type, m.pdf
from public.message m;

insert into gko.response_file(response_id, response_file_content, response_file_path, response_file_type)
select gr.response_id,
       jsonb_build_object('cad_num', fd.cad_num, 'group', fd."group"),
       fd.decription, 'efd'
from public.out_fd fd
         join acts a on a.id = fd.acts_id
         join message m on m.id = a.message_id
         join gko.response gr on gr.response_date=m.date_in and gr.response_name=m.name;

insert into gko.response_file(response_id, response_file_content, response_file_path, response_file_type)
select gr.response_id,
       ox.xml,
       ox.decription, 'exml'
from public.out_xmls ox
         join acts a on a.id = ox.acts_id
         join message m on m.id = a.message_id
         join gko.response gr on gr.response_date=m.date_in and gr.response_name=m.name;

insert into gko.response_act(response_act_ods, response_act_ods_filename, response_act_count_ok, response_act_count_bad, response_id)
select a.ods, a.ods_name, a.count_ok, a.count_bad, gr.response_id
from public.acts a
         join message m on m.id = a.message_id
         join gko.response gr on gr.response_date=m.date_in and gr.response_name=m.name;

insert into gko.response_parcel(response_parcel_file_id, response_parcel_cad_num, response_parcel_cost, response_parcel_upks, response_parcel_group)
with parcel_obj as (
    select rfc.response_file_id, r.response_id,
           jsonb_path_query(rfc.response_file_content, '$.**."Cadastral_Block"."Parcels"."Parcel"[*]'::jsonpath) AS obj
    from gko.response r
             join gko.response_file rfc on r.response_id = rfc.response_id and rfc.response_file_type='exml'
),
     parcel_cost as (     select parcel_obj.response_file_id,
                                 parcel_obj.response_id,
                                 btrim(jsonb_path_query(parcel_obj.obj, '$.**."@CadastralNumber"'::jsonpath)::text, '"'::text) AS cad_num,
                                 substring(replace((jsonb_path_query(parcel_obj.obj, '$.**."Ground_Payments"[*]."CadastralCost"."@Value"'::jsonpath) ->> 0), ',', '.'), '[0-9\.]+')::numeric AS cost,
                                 substring(replace((jsonb_path_query(parcel_obj.obj, '$.**."Ground_Payments"[*]."Specific_CadastralCost"."@Value"'::jsonpath) ->> 0), ',', '.'), '[0-9\.]+')::numeric AS upks
                          from parcel_obj

     ),
     parcel_fd as(
         select
             rfd.response_id,
             jsonb_path_query(rfd.response_file_content, '$.**."cad_num"'::jsonpath) ->> 0 AS cad_num,
             jsonb_path_query(rfd.response_file_content, '$.**."group"'::jsonpath) ->> 0 AS name_group
         from gko.response_file rfd
         where rfd.response_file_type = 'efd'
     )

select parcel_cost.response_file_id,
       parcel_cost.cad_num,
       parcel_cost.cost,
       parcel_cost.upks,
       parcel_fd.name_group
from parcel_cost
         left join parcel_fd on parcel_fd.cad_num = parcel_cost.cad_num and parcel_fd.response_id=parcel_cost.response_id;


insert into gko.response_code(response_code_code, response_code_cad_num, response_code_date)
select code, cad_num, date
from public.code_obj;

with codes as (
    select distinct c.response_code_date::date as date
    from gko.response_code c
),
     responses as (
         select r.response_date::date as date, r.response_id
         from gko.response r
     ),
     codes_to_responses as (
         select codes.date as cdate, responses.response_id as response_id
         from codes
                  left join responses on responses.date = codes.date
     )
update gko.response_code
set response_code_response_id = codes_to_responses.response_id
from codes_to_responses
where response_code_date::date = codes_to_responses.cdate;

insert into gko.response(response_name, response_date, response_type_id, response_pdf)
select distinct on (m.name, m.date_in) m.name, m.date_in, 0 as type, m.pdf
from public.message m;

-- псоле всего
with resp as(
    select m.date_out, m.date_in, m.name
    from public.message m
)
update gko.response r
set response_date = resp.date_out
from resp
where resp.name=r.response_name and r.response_date=resp.date_in;

with resp as(
    select m.date_in, m.name
    from public.message m
)
update gko.response r
set response_date = resp.date_in
from resp
where resp.name=r.response_name and r.response_date is null;

create table gko.history_all_union(
  cad_num text,
  "Судебный?" text,
  cad_num_quarter text,
  date_created text,
  foundation_date text,
  parent_cad_num text,
  parent_year_built text,
  parent_year_used text,
  parent_object_type text,
  parent_assignation_building text,
  parent_cadastral_numbers text,
  inner_cadastral_numbers text,
  cost_old text,
  utilization_cod_old text,
  utilization_cod_new text,
  utilization text,
  utilization_doc text,
  purpose text,
  category text,
  vid text,
  name text,
  area text,
  okato text,
  fias text,
  wall text,
  kladr text,
  address1 text,
  address2 text,
  percent text,
  year_built text,
  year_used text,
  floors text,
  length text,
  depth text,
  volume text,
  height text,
  square text,
  builtsquare text,
  depthoo text,
  id text,
  file_name text,
  date_in text,
  name_in text,
  path text,
  date_rosreestr_out text,
  id_xml text,
  acts_id text,
  m_id text,
  a_id text,
  m_date_in text,
  m_name_in text,
  m_date_out text,
  m_name text,
  cost text,
  upks text,
  id_fd text,
  "group" text,
  code text,
  code_name text,
  db_nam text
);