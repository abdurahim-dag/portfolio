CREATE SCHEMA if not exists gko;

SET search_path TO gko,public;
ALTER ROLE app SET search_path TO gko,public;

CREATE OR REPLACE FUNCTION gko.map_class_arr(in_array jsonb)
    RETURNS text
    LANGUAGE plpgsql
AS $function$
DECLARE
    js jsonb := in_array;
    i text;
    result_ids TEXT[];

    wall_value text;
    wall_code text;
BEGIN

    FOR i IN SELECT * FROM jsonb_array_elements_text(js)
        LOOP
            wall_code := TRIM(i);
            SELECT INTO wall_value value FROM gko.classification WHERE code = wall_code;
            IF NOT FOUND THEN
                wall_value := wall_code;
            END IF;
            IF wall_value is not null THEN
                result_ids  := array_append(result_ids, wall_value);
            END IF;
        END LOOP;
    i = array_to_string(result_ids, ',');
    RETURN i;
END;
$function$
;

CREATE OR REPLACE FUNCTION gko.map_class(in_ text)
    RETURNS text
    LANGUAGE plpgsql
AS $function$
DECLARE
    value_ text;
BEGIN

    SELECT INTO value_ value FROM gko.classification WHERE code = TRIM(in_);
    IF NOT FOUND THEN
        value_ := in_;
    END IF;

    RETURN value_;

END;
$function$
;
