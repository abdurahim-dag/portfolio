select
    parcel_cad_num as "Кадастровый номер",
    parcel_cad_num_quarter as "Кадастровый номер квартала",
    parcel_date_created as "Дата присвоения кадастрового номера",
    parcel_foundation_date as "Дата возникновения оснований",
    parcel_parent_cad_num as "Родит. КН",
    parcel_parent_year_built as "Родит. дата заверш. строит.",
    parcel_parent_year_used as "Родит. дата ввода в эксплуат.",
    parcel_parent_object_type as "Родит. вид объекта",
    parcel_parent_assignation_building as "Родит. назначение здания",
    parcel_parent_cadastral_numbers as "КН в пределах кот. распол.",
    parcel_inner_cadastral_numbers as "Кадастровые номера расположенных в пределах земельного участка",
    parcel_cost_old as "Текущая КС",
    parcel_utilization_cod_old as "ВРИ ранее использ. класс.",
    parcel_utilization_cod_new as "ВРИ по класс.",
    parcel_utilization as "ВРИ текст",
    parcel_utilization_doc as "ВРИ по документу",
    parcel_purpose as "Разрешенное использование",
    parcel_category as "Категория",
    parcel_vid as "Вид",
    parcel_name as "Наименование",
    parcel_area as "Площадь",
    parcel_wall as "Материал стен",
    parcel_okato as "ОКАТО",
    parcel_fias as "ФИАС",
    parcel_kladr as "КЛАДР",
    parcel_address_1 as "Адрес1",
    parcel_address_2 as "Адрес2",
    parcel_percent as "% заверш.",
    parcel_year_built as "Дата заверш. строит.",
    parcel_year_used as "Дата ввода в эксплуат.",
    parcel_floors as "Этажей",
    parcel_length as "Протяженность",
    parcel_depth as "Глубина",
    parcel_volume as "Объем",
    parcel_height as "Высота",
    parcel_square as "Площадь_",
    parcel_builtsquare as "Площадь застройки",
    parcel_depthoo as "Глубина залегания",
    parcel_date_rosreestr_out as "Дата выгрузки рееста",
    r.request_date as "Дата поступления реестра",
    r.request_name as "Наименование реестра"
from gko.parcel
         join request_file rf on rf.request_file_id = parcel.parcel_request_file_id
         join request r on r.request_id = rf.request_id
where r.request_date >= '{dt}' and r.request_date <= '{dt}'