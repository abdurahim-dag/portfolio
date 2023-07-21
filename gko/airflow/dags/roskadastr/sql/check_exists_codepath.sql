select response_code_file_id
from gko.response_code_file
where response_code_file_path=%(path)s
limit 1;