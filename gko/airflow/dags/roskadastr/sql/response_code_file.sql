insert into gko.response_code_file(response_code_file_name, response_code_file_path, response_code_file_date)
values (%(file_name)s, %(path)s, %(date)s)
RETURNING response_code_file_id;