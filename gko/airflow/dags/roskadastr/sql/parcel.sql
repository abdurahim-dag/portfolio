with requests as (
    select
        rf.request_file_id,
        r.request_name,
        r.request_date,
        rf.request_file_name,
        rf.request_file_path,
        rf.request_file_content,
        rf.request_file_options
    from gko.request_file rf
             join gko.request r on r.request_id = rf.request_id
    where rf.request_file_id = {0}
),
     requests_xml as (
         select *, jsonb_path_query(request_file_content, '$."ListForRating"."Objects".*.*[*]'::jsonpath) AS obj
         from requests
         where requests.request_file_name like '%.xml%'
     ),
     requests_xls as (
         select *, jsonb_array_elements(request_file_content) AS obj
         from requests
         where requests.request_file_name like '%.xlsx%'
     )

insert into gko.parcel(
    parcel_cad_num, parcel_address_1, parcel_address_2, parcel_category, parcel_cad_num_quarter, parcel_date_created,
    parcel_foundation_date, parcel_parent_cad_num, parcel_parent_year_built, parcel_parent_year_used,
    parcel_parent_object_type, parcel_parent_assignation_building, parcel_parent_cadastral_numbers,
    parcel_inner_cadastral_numbers, parcel_cost_old, parcel_utilization_cod_old,
    parcel_utilization_cod_new, parcel_utilization, parcel_utilization_doc, parcel_purpose,
    parcel_vid, parcel_name, parcel_area, parcel_wall, parcel_okato, parcel_fias, parcel_kladr,
    parcel_percent, parcel_year_built, parcel_year_used, parcel_floors, parcel_length, parcel_depth,
    parcel_volume, parcel_height, parcel_square, parcel_builtsquare, parcel_depthoo,
    parcel_date_rosreestr_out, parcel_request_file_id)
SELECT
        jsonb_path_query(requests.obj, '$."@CadastralNumber"'::jsonpath) ->> 0 AS cad_num,
        jsonb_path_query(requests.obj, '$."Location".**."Note"'::jsonpath) ->> 0 AS address1,
        regexp_replace(concat(jsonb_path_query(requests.obj, '$."Location".**."District"."@Type"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."District"."@Name"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."City"."@Type"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."City"."@Name"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."UrbanDistrict"."@Type"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."UrbanDistrict"."@Name"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."SovietVillage"."@Type"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."SovietVillage"."@Name"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."Locality"."@Type"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."Locality"."@Name"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."Street"."@Type"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."Street"."@Name"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."Level1"."@Type"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."Level1"."@Value"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."Level2"."@Type"'::jsonpath) ->> 0, jsonb_path_query(requests.obj, '$."Location".**."Level2"."@Value"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."Level3"."@Type"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."Level3"."@Name"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."Apartment"."@Type"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."Apartment"."@Value"'::jsonpath) ->> 0, ' ', jsonb_path_query(requests.obj, '$."Location".**."@Other"'::jsonpath) ->> 0), '\s+'::text, ' '::text, 'g'::text) AS address2,
        map_class(jsonb_path_query(requests.obj, '$."Category"'::jsonpath) ->> 0) AS category,
        jsonb_path_query(requests.obj, '$."CadastralBlock"'::jsonpath) ->> 0 AS cad_num_quarter,
        (jsonb_path_query(requests.obj, '$."@DateCreated"'::jsonpath) ->> 0)::timestamptz AS date_created,
        (jsonb_path_query(requests.obj, '$."@FoundationDate"'::jsonpath) ->> 0)::timestamptz AS foundation_date,
        jsonb_path_query(requests.obj, '$."ParentOKS"."CadastralNumberOKS"'::jsonpath) ->> 0 AS parent_cad_num,
        jsonb_path_query(requests.obj, '$."ParentOKS"."ExploitationChar"."@YearBuilt"'::jsonpath) ->> 0 AS parent_year_built,
        jsonb_path_query(requests.obj, '$."ParentOKS"."ExploitationChar"."@YearUsed"'::jsonpath) ->> 0 AS parent_year_used,
        map_class(jsonb_path_query(requests.obj, '$."ParentOKS"."ObjectType"'::jsonpath) ->> 0) AS parent_object_type,
        map_class(jsonb_path_query(requests.obj, '$."ParentOKS"."AssignationBuilding"'::jsonpath) ->> 0) AS parent_assignation_building,
        map_class_arr(jsonb_path_query_array(jsonb_path_query(requests.obj, '$.**."ParentCadastralNumbers"'::jsonpath), '$.**."CadastralNumber"'::jsonpath)) AS parent_cadastral_numbers,
        map_class_arr(jsonb_path_query_array(jsonb_path_query(requests.obj, '$.**."InnerCadastralNumbers"'::jsonpath), '$.**."CadastralNumber"'::jsonpath)) AS inner_cadastral_numbers,
        jsonb_path_query(requests.obj, '$."CadastralCost"."@Value"'::jsonpath) ->> 0 AS cost_old,
        map_class(jsonb_path_query(requests.obj, '$.**."Utilization"."@Utilization"'::jsonpath) ->> 0) AS utilization_cod_old,
        map_class(jsonb_path_query(requests.obj, '$.**."Utilization"."@LandUse"'::jsonpath) ->> 0) AS utilization_cod_new,
        to_json(
            array_remove(
                ARRAY[
                    jsonb_path_query(requests.obj, '$.**."Utilization"."@PermittedUseText"'::jsonpath),
                    jsonb_path_query_array(jsonb_path_query(requests.obj, '$.**."ObjectPermittedUses"'::jsonpath),'$.**."ObjectPermittedUse"'::jsonpath),
                    jsonb_path_query(requests.obj, '$.**."PositionInObject"."@Number"'::jsonpath)
                    ], NULL::jsonb)) ->> 0 AS utilization,
        jsonb_path_query(requests.obj, '$.**."Utilization"."@ByDoc"'::jsonpath) ->> 0 AS utilization_doc,
        map_class(to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$."AssignationBuilding"'::jsonpath), jsonb_path_query(requests.obj, '$."AssignationName"'::jsonpath), jsonb_path_query(requests.obj, '$."Assignation"."AssignationCode"'::jsonpath)], NULL::jsonb)) ->> 0) AS purpose,
        map_class(jsonb_path_query(requests.obj, '$."ObjectType"'::jsonpath) ->> 0) AS vid,
        map_class(jsonb_path_query(requests.obj, '$."Name"'::jsonpath) ->> 0) AS name,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$."Area"."Area"'::jsonpath), jsonb_path_query(requests.obj, '$."Area"'::jsonpath)], NULL::jsonb)) ->> 0 AS area,
        map_class_arr(jsonb_path_query_array(jsonb_path_query(requests.obj, '$.**."Material"'::jsonpath), '$.**."@Wall"'::jsonpath)) AS wall,
        jsonb_path_query(requests.obj, '$."Location".**."OKATO"'::jsonpath) ->> 0 AS okato,
        jsonb_path_query(requests.obj, '$."Location".**."FIAS"'::jsonpath) ->> 0 AS fias,
        jsonb_path_query(requests.obj, '$."Location".**."KLADR"'::jsonpath) ->> 0 AS kladr,
        jsonb_path_query(requests.obj, '$."DegreeReadiness"'::jsonpath) ->> 0 AS percent,
        jsonb_path_query(requests.obj, '$."ExploitationChar"."@YearBuilt"'::jsonpath) ->> 0 AS year_built,
        jsonb_path_query(requests.obj, '$."ExploitationChar"."@YearUsed"'::jsonpath) ->> 0 AS year_used,
        jsonb_path_query(requests.obj, '$."Floors"."@Floors"'::jsonpath) ->> 0 AS floors,
        jsonb_path_query(requests.obj, '$.**."KeyParameters"[*]."KeyParameter"?(@."@Type" == "01")."@Value"'::jsonpath) ->> 0 AS length,
        jsonb_path_query(requests.obj, '$.**."KeyParameters"[*]."KeyParameter"?(@."@Type" == "02")."@Value"'::jsonpath) ->> 0 AS depth,
        jsonb_path_query(requests.obj, '$.**."KeyParameters"[*]."KeyParameter"?(@."@Type" == "03")."@Value"'::jsonpath) ->> 0 AS volume,
        jsonb_path_query(requests.obj, '$.**."KeyParameter"?(@."@Type" == "04")."@Value"'::jsonpath) ->> 0 AS height,
        jsonb_path_query(requests.obj, '$.**."KeyParameters"[*]."KeyParameter"?(@."@Type" == "05")."@Value"'::jsonpath) ->> 0 AS square,
        jsonb_path_query(requests.obj, '$.**."KeyParameters"[*]."KeyParameter"?(@."@Type" == "06")."@Value"'::jsonpath) ->> 0 AS builtsquare,
        jsonb_path_query(requests.obj, '$.**."KeyParameters"[*]."KeyParameter"?(@."@Type" == "07")."@Value"'::jsonpath) ->> 0 AS depthoo,
        "substring"(requests.request_file_options::text, '.*@DateForm\": \"(.*?)\",.*'::text)::date AS date_rosreestr_out,
        requests.request_file_id
FROM requests_xml as requests
UNION ALL
SELECT
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."КАД №" != null)."КАД №"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."КАД. №" != null)."КАД. №"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."КАДАСТРОВЫЙ № ОКС" != null)."КАДАСТРОВЫЙ № ОКС"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."КАДАСТРОВЫЙ НОМЕР ОКС" != null)."КАДАСТРОВЫЙ НОМЕР ОКС"'::jsonpath)], NULL::jsonb)) ->> 0 AS cad_num,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."АДРЕС 1" != null)."АДРЕС 1"'::jsonpath)], NULL::jsonb)) ->> 0 AS address1,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."АДРЕС 2" != null)."АДРЕС 2"'::jsonpath)], NULL::jsonb)) ->> 0 AS address2,
        map_class(to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."КАТЕГОРИЯ" != null)."КАТЕГОРИЯ"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."КОД КАТЕГОРИИ" != null)."КОД КАТЕГОРИИ"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."КАТЕГОРИЯ НЕЗАСВИД." != null)."КАТЕГОРИЯ НЕЗАСВИД."'::jsonpath)], NULL::jsonb)) ->> 0) AS category,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."№ КАД. КВАРТАЛА" != null)."№ КАД. КВАРТАЛА"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."КАД. КВАРТАЛ" != null)."КАД. КВАРТАЛ"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."НОМЕР КАД. КВАРТАЛА" != null)."НОМЕР КАД. КВАРТАЛА"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."КАД. КВАРТАЛ ОКС" != null)."КАД. КВАРТАЛ ОКС"'::jsonpath)], NULL::jsonb)) ->> 0 AS cad_num_quarter,
        NULL AS date_created,
        NULL AS foundation_date,
        NULL AS parent_cad_num,
        NULL AS parent_year_built,
        NULL AS parent_year_used,
        NULL AS parent_object_type,
        NULL AS parent_assignation_building,
        NULL AS parent_cadastral_numbers,
        NULL AS inner_cadastral_numbers,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."КРАЙНЯЯ КАДАСТРОВАЯ СТОИМОСТЬ" != null)."КРАЙНЯЯ КАДАСТРОВАЯ СТОИМОСТЬ"'::jsonpath)], NULL::jsonb)) ->> 0 AS cost_old,
        map_class(to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."КОД ВРИ ПО П/389" != null)."КОД ВРИ ПО П/389"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."КОД ВРИ КЛ. РР" != null)."КОД ВРИ КЛ. РР"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."КОД ВРИ РР" != null)."КОД ВРИ РР"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."КОД ВРИ РР НЕЗАСВИД." != null)."КОД ВРИ РР НЕЗАСВИД."'::jsonpath)], NULL::jsonb)) ->> 0) AS utilization_cod_old,
        map_class(to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."КОД ВРИ МЭР" != null)."КОД ВРИ МЭР"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."КОД ВРИ МЭР НЕЗАСВИД." != null)."КОД ВРИ МЭР НЕЗАСВИД."'::jsonpath)], NULL::jsonb)) ->> 0) AS utilization_cod_new,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."ВРИ КЛ. РР" != null)."ВРИ КЛ. РР"'::jsonpath)], NULL::jsonb)) ->> 0 AS utilization,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."ВРИ ПО ДОКУМ" != null)."ВРИ ПО ДОКУМ"'::jsonpath)], NULL::jsonb)) ->> 0 AS utilization_doc,
        map_class(to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."КОД НАЗНАЧЕНИЯ" != null)."КОД НАЗНАЧЕНИЯ"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."НАЗНАЧЕНИЕ" != null)."НАЗНАЧЕНИЕ"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."НАЗНАЧЕНИЕ ОКС" != null)."НАЗНАЧЕНИЕ ОКС"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."НАЗНАЧЕНИЕ ТЕКСТ" != null)."НАЗНАЧЕНИЕ ТЕКСТ"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."НАЗНАЧЕНИЕ ТЕКСТ ОКС" != null)."НАЗНАЧЕНИЕ ТЕКСТ ОКС"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."НАЗНАЧЕНИЕ ЕНК" != null)."НАЗНАЧЕНИЕ ЕНК"'::jsonpath)], NULL::jsonb)) ->> 0) AS purpose,
        map_class(to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."ВИД ОН" != null)."ВИД ОН"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."ВИД ОКС" != null)."ВИД ОКС"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."ВИД ОБЪЕКТА" != null)."ВИД ОБЪЕКТА"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."КОД ВИДА ОКС" != null)."КОД ВИДА ОКС"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."КОД ВИДА ОБЪЕКТА" != null)."КОД ВИДА ОБЪЕКТА"'::jsonpath)], NULL::jsonb)) ->> 0) AS vid,
        map_class(to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."НАИМЕНОВАНИЕ ОКС" != null)."НАИМЕНОВАНИЕ ОКС"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."НАИМЕНОВАНИЕ ОКН" != null)."НАИМЕНОВАНИЕ ОКН"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."НАИМЕНОВАНИЕ ОБЪЕКТА" != null)."НАИМЕНОВАНИЕ ОБЪЕКТА"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."НАИМЕНОВАНИЕ" != null)."НАИМЕНОВАНИЕ"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."НАИМЕНОВАНИЕ ЕНК" != null)."НАИМЕНОВАНИЕ ЕНК"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."ВИД ЗУ" != null)."ВИД ЗУ"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."ТИП ПОМЕЩЕНИЯ" != null)."ТИП ПОМЕЩЕНИЯ"'::jsonpath)], NULL::jsonb)) ->> 0) AS name,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."ПЛОЩАДЬ" != null)."ПЛОЩАДЬ"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."ПЛОЩАДЬ ЗУ" != null)."ПЛОЩАДЬ ЗУ"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."ПЛОЩАДЬ ОКС" != null)."ПЛОЩАДЬ ОКС"'::jsonpath)], NULL::jsonb)) ->> 0 AS area,
        map_class_arr(jsonb_build_array(jsonb_path_query(requests.obj, '$[*]?(@."МАТЕРИАЛ СТЕН" != null)."МАТЕРИАЛ СТЕН"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."МАТЕРИАЛ СТЕН ОКС" != null)."МАТЕРИАЛ СТЕН ОКС"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."КОД МАТЕРИАЛА СТЕН ОКС" != null)."КОД МАТЕРИАЛА СТЕН ОКС"'::jsonpath))) AS wall,
        NULL AS okato,
        NULL AS fias,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."КЛАДР" != null)."КЛАДР"'::jsonpath)], NULL::jsonb)) ->> 0 AS kladr,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."СТЕПЕНЬ ГОТОВНОСТИ ОКС" != null)."СТЕПЕНЬ ГОТОВНОСТИ ОКС"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."СТЕПЕНЬ ГОТОВНОСТИ" != null)."СТЕПЕНЬ ГОТОВНОСТИ"'::jsonpath)], NULL::jsonb)) ->> 0 AS percent,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."ГОД ЗАВЕРШЕНИЯ СТРОИТЕЛЬСТВА" != null)."ГОД ЗАВЕРШЕНИЯ СТРОИТЕЛЬСТВА"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."ГОД ЗАВЕРШЕНИЯ СТРОИТЕЛЬСТВА ОКС" != null)."ГОД ЗАВЕРШЕНИЯ СТРОИТЕЛЬСТВА ОКС"'::jsonpath)], NULL::jsonb)) ->> 0 AS year_built,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."ГОД ВВОДА В ЭКСПЛУАТАЦИЮ" != null)."ГОД ВВОДА В ЭКСПЛУАТАЦИЮ"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."ГОД ВВОДА В ЭКСПЛУАТАЦИЮ ОКС" != null)."ГОД ВВОДА В ЭКСПЛУАТАЦИЮ ОКС"'::jsonpath)], NULL::jsonb)) ->> 0 AS year_used,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."ЭТАЖ" != null)."ЭТАЖ"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."Общая этажность ОКС" != null)."Общая этажность ОКС"'::jsonpath)], NULL::jsonb)) ->> 0 AS floors,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."ПРОТЯЖЕННОСТЬ ОКС" != null)."ПРОТЯЖЕННОСТЬ ОКС"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."ПРОТЯЖЕННОСТЬ" != null)."ПРОТЯЖЕННОСТЬ"'::jsonpath)], NULL::jsonb)) ->> 0 AS length,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."ГЛУБИНА ОКС" != null)."ГЛУБИНА ОКС"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."ГЛУБИНА" != null)."ГЛУБИНА"'::jsonpath)], NULL::jsonb)) ->> 0 AS depth,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."ОБЪЕМ ОКС" != null)."ГЛУБИНА ОКС"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."ОБЪЕМ" != null)."ОБЪЕМ"'::jsonpath)], NULL::jsonb)) ->> 0 AS volume,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."ВЫСОТА ОКС" != null)."ВЫСОТА ОКС"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."ВЫСОТА" != null)."ВЫСОТА"'::jsonpath)], NULL::jsonb)) ->> 0 AS height,
        NULL AS square,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."ПЛ.ЗАСТРОЙКИ" != null)."ПЛ.ЗАСТРОЙКИ"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."ПЛ.ЗАСТРОЙКИ ОКС" != null)."ПЛ.ЗАСТРОЙКИ ОКС"'::jsonpath)], NULL::jsonb)) ->> 0 AS builtsquare,
        to_json(array_remove(ARRAY[jsonb_path_query(requests.obj, '$[*]?(@."ГЛУБИНА ЗАЛЕГАНИЯ ОКС" != null)."ГЛУБИНА ЗАЛЕГАНИЯ ОКС"'::jsonpath), jsonb_path_query(requests.obj, '$[*]?(@."ГЛУБИНА ЗАЛЕГАНИЯ" != null)."ГЛУБИНА ЗАЛЕГАНИЯ"'::jsonpath)], NULL::jsonb)) ->> 0 AS depthoo,
        "substring"(requests.request_file_options::text, '.*@DateForm\": \"(.*?)\",.*'::text)::date AS date_rosreestr_out,
        requests.request_file_id
FROM requests_xls as requests;