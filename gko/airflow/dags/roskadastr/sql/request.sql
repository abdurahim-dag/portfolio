insert into gko.request(request_date, request_reg_num, request_type_id, request_name, request_description, request_pdf)
VALUES (%(date)s, %(reg_num)s, %(type_id)s, %(name)s, %(descr)s, %(pdf)s)
RETURNING request_id;