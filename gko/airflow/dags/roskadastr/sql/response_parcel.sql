insert into gko.response_parcel(response_parcel_file_id, response_parcel_cad_num, response_parcel_cost, response_parcel_upks, response_parcel_group)
with parcel_obj as (
    select rfc.response_file_id, r.response_id,
           jsonb_path_query(rfc.response_file_content, '$.**."Cadastral_Block"."Parcels"."Parcel"[*]'::jsonpath) AS obj
    from gko.response r
             join gko.response_file rfc on r.response_id = rfc.response_id and rfc.response_file_type='cost'
    where r.response_id={0}
),
     parcel_cost as(
         select parcel_obj.response_file_id,
                parcel_obj.response_id,
                btrim(jsonb_path_query(parcel_obj.obj, '$.**."@CadastralNumber"'::jsonpath)::text, '"'::text) AS cad_num,
                (jsonb_path_query(parcel_obj.obj, '$.**."Ground_Payments"[*]."CadastralCost"."@Value"'::jsonpath) ->> 0)::numeric AS cost,
                (jsonb_path_query(parcel_obj.obj, '$.**."Ground_Payments"[*]."Specific_CadastralCost"."@Value"'::jsonpath) ->> 0)::numeric AS upks
         from parcel_obj
     ),
     parcel_fd_groups as(
         select distinct
             rfd.response_id,
             jsonb_path_query(rfd.response_file_content, '$.**."Group_Real_Estate".**."ID_Group"'::jsonpath) AS id_group,
             jsonb_path_query(rfd.response_file_content, '$.**."Group_Real_Estate".**."Name_Group"'::jsonpath)::text AS name_group
         from gko.response_file rfd
         where rfd.response_file_type = 'fd'
     ),
     parcel_fd_cad_nums as(
         select distinct
             rfd.response_id,
             btrim(jsonb_path_query(rfd.response_file_content, '$.**."Real_Estate".**."CadastralNumber"'::jsonpath)::text, '"'::text) AS cad_num,
             jsonb_path_query(rfd.response_file_content, '$.**."Real_Estate".**."@ID_Group"'::jsonpath) AS id_group
         from gko.response_file rfd
         where rfd.response_file_type = 'fd'
     ),
     parcel_fd as (
         select cn.cad_num, cn.response_id, g.name_group
         from parcel_fd_cad_nums cn
                  left join parcel_fd_groups g on g.id_group = cn.id_group and g.response_id=cn.response_id
     )

select parcel_cost.response_file_id,
       parcel_cost.cad_num,
       parcel_cost.cost,
       parcel_cost.upks,
       parcel_fd.name_group
from parcel_cost
         left join parcel_fd on parcel_fd.cad_num = parcel_cost.cad_num and parcel_fd.response_id=parcel_cost.response_id