from pydantic import BaseModel, Json
from pendulum import DateTime, parse, datetime, Date
import decimal

class Request(BaseModel):
    request_date: str
    request_reg_num: str
    request_type_id: int
    request_name: str
    request_description: str
    request_pdf: str


class RequestFile(BaseModel):
    request_file_name: str
    request_file_path: str
    request_file_content: Json
    request_file_options: str
    request_file_description: str = ''


class Response(BaseModel):
    response_name: str
    response_date: str
    response_reg_num: str = ''
    response_description: str
    response_type_id: int
    response_pdf: str

class ResponseFile(BaseModel):
    response_file_name: str
    response_file_content: Json
    response_file_path: str
    response_file_description: str = ''
    response_file_type: str

class ResponseAct(BaseModel):
    response_act_ods_filename: str
    response_act_count_ok: int
    response_act_count_bad: int
    response_act_ods_path: str
