"""Выгрузка из бонусной системы в DWH"""
import datetime
import logging
import pathlib

import pendulum
import os
import re

import requests
from airflow import DAG
from airflow.decorators import task
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.samba.hooks.samba import SambaHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.decorators import task
import mmap
import json
from airflow.models.variable import Variable
from airflow.models.connection import Connection
from roskadastr.xml_read import Reader
import roskadastr.models as models
import psycopg
import pandas as pd
import xlsxwriter


args = {
    'owner': 'ragim',
    'email': ['ragimatamov@yandex.ru'],
    'email_on_failure': False,
    'email_on_retry': False,
}

SMB_BASEDIR = Variable.get('SMB_DAYS')
LOCAL_DIR_EXPORT = os.path.join(Variable.get('DATA_DIR'), 'export')
SQL_DIR = 'SQL_DIR'

conn = Connection.get_connection_from_secrets('email_exchange')
server = conn.host
email = conn.schema
username = conn.login
password = conn.password


conn = Connection.get_connection_from_secrets('smb_public')
smb_server = conn.host
smb_username = conn.login
smb_password = conn.password

CONN_PG_ID = 'PG_GKO'


# def check(dag_id, task_id, exec_dt):
#     last_dag_run = DagRun.find(dag_id=dag_id, execution_date=exec_dt)
#     if last_dag_run:
#         status = last_dag_run.get_task_instances(task_id).state
#         logging.warning(status)


def load(ds, folder: str, v_sql_id: str):
    folder = os.path.join(folder, ds)
    hook = PostgresHook(CONN_PG_ID)
    uri = hook.get_uri()
    conn: psycopg.Connection
    curs: psycopg.Cursor

    sql_request = open(os.path.join(Variable.get(v_sql_id), 'request.sql'), encoding='utf8').read()
    sql_request_file = open(os.path.join(Variable.get(v_sql_id), 'request_file.sql'), encoding='utf8').read()

    reader = Reader(
        folder=folder,
        type_id=16,
        reg_num=''
    )
    with psycopg.connect(uri) as conn:
        conn.autocommit = False
        with conn.cursor() as curs:
            for el in reader.get():
                if isinstance(el, models.Request):
                    file_pdf = open(el.request_pdf, 'rb').read()
                    pdf = psycopg.Binary(file_pdf)
                    curs.execute(
                        sql_request,
                        {
                            'date': el.request_date,
                            'reg_num': el.request_reg_num,
                            'type_id': str(el.request_type_id),
                            'name': el.request_name,
                            'descr': el.request_description,
                            'pdf': pdf
                        },
                    )
                    request_id = curs.fetchone()[0]
                    conn.commit()
                elif isinstance(el, models.RequestFile):
                    content = json.dumps(el.request_file_content, ensure_ascii=False)
                    content = re.sub(r"\t", "", content)
                    content = re.sub(r"\r", "", content)
                    content = re.sub(r"\n", "", content)
                    curs.execute(
                        sql_request_file,
                        {
                         'file_name': el.request_file_name,
                         'path': el.request_file_path,
                         'req_id': str(request_id),
                         'options': el.request_file_options,
                         'descr': el.request_file_description,
                         'content': content,
                        }
                    )
                    conn.commit()

def update(ds, v_sql_id: str):
    hook = PostgresHook(CONN_PG_ID)
    uri = hook.get_uri()
    conn: psycopg.Connection
    curs: psycopg.Cursor

    sql_parcel = open(os.path.join(Variable.get(v_sql_id), 'parcel.sql'), encoding='utf8').read()
    sql_rejected = open(os.path.join(Variable.get(v_sql_id), 'rejected.sql'), encoding='utf8').read()
    sql_get_request_dt = open(os.path.join(Variable.get(v_sql_id), 'get_request_by_date.sql'), encoding='utf8').read()
    sql_get_request_file_id = open(os.path.join(Variable.get(v_sql_id), 'get_request_file_by_id.sql'), encoding='utf8').read()

    with psycopg.connect(uri) as conn:
        conn.autocommit = False
        with conn.cursor() as curs:
            curs.execute(sql_get_request_dt,{'dt': ds})
            request_ids = curs.fetchall()
            request_ids = [r[0] for r in request_ids]
            for request_id in request_ids:
                logging.info('Start update for request_id=%s', request_id)
                curs.execute(sql_get_request_file_id, {'request_id': request_id})
                request_file_ids = curs.fetchall()
                request_file_ids = [r[0] for r in request_file_ids]
                for request_file_id in request_file_ids:
                    logging.info('Start update for request_file_id=%s',request_file_id)
                    try:
                        curs.execute(sql_parcel.format(request_file_id))
                        conn.commit()
                        logging.info("Rows affected: %s", curs.rowcount)
                    except Exception as e:
                        conn.rollback()
                        logging.info(re.escape(str(e)))
                        curs.execute(
                            sql_rejected,
                            ('gko.parcel', re.escape(str(e)), 'gko.request_file', '', request_file_id, pendulum.now())
                        )
                        conn.commit()


def export(ds, conn_id, v_sql_id, dst_folder):
    logging.warning(f"Start export for date {ds}!")
    hook = PostgresHook(conn_id)
    uri = hook.get_uri()
    conn: psycopg.Connection
    sql = open(os.path.join(Variable.get(v_sql_id), 'export.sql'), encoding='utf8').read().format(dt=ds)

    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)

    with psycopg.connect(uri) as conn:
        df_all = pd.read_sql(sql, conn)
        logging.warning(f"Count rows selected {df_all.shape[0]}!")
        vid = df_all["Вид"].unique()
        name = 'Все'
        logging.warning(f"Generate files for {vid}!")
        for v in vid:
            file_path = os.path.join(dst_folder, f"{ds}-{v}.xlsx")
            logging.warning(f"Generate files {file_path}!")
            with xlsxwriter.Workbook(file_path) as workbook:
                df_all = df_all.fillna('')

                df1 = df_all[df_all["Вид"] == v]

                bold = workbook.add_format({'bold': True})
                default = workbook.add_format()
                worksheet = workbook.add_worksheet(name)
                heads = list(df1.columns.values)

                col = -1

                for h in heads:
                    check = df1[h].unique()
                    if len(check) == 0 or (len(check) == 1 and check[0] == ''):
                        continue
                    col += 1
                    worksheet.write(0, col, h, bold)
                    row = 0
                    headers = df1[h].items()
                    for _, item in headers:
                        if isinstance(item, type(pd.NaT)):
                            item = ''
                        row += 1
                        worksheet.write(row, col, str(item))

    logging.info("End export!")

with DAG(
        'get-request-dag',
        catchup=False,
        default_args=args,
        description='Dag for load requests from exchange email to pg',
        is_paused_upon_creation=True,
        start_date=pendulum.datetime(2022, 5, 5, tz="UTC"),
        schedule_interval='0 0 * * *',  # Задаем расписание выполнения дага.
        tags=['request', ],
) as dag:
    start = EmptyOperator(task_id='start')
    end = EmptyOperator(task_id='end')

    t_get_attachments = BashOperator(
        task_id='get_attcachments_task',
        bash_command="python /opt/airflow/dags/roskadastr/get_attachments.py {{ ds }} '{{params.dst}}/{{ ds }}' {{params.server}} {{params.email}} '{{params.username}}' {{params.password}}",
        params = {
            'dst': os.path.join(Variable.get('DATA_DIR'), 'in'),
            'server': server,
            'email': email,
            'username': username,
            'password': password
        },
        dag=dag
    )

    @task.branch
    def choose_branch(date_start: str, path_to: str):
        logging.info(path_to)
        path = pathlib.Path(path_to)
        if list(path.glob('**/*.zip')) or list(path.glob('**/*.rar')):
            logging.info(list(path.glob('*')))
            if requests.get(f"https://isdayoff.ru/{date_start.replace('-', '')}").text == '0':
                return ['copy_to_smb_task']
        return ['end']


    t_copy_to_smb = BashOperator(
        task_id='copy_to_smb_task',
        bash_command="python /opt/airflow/dags/roskadastr/attachments_tosmb.py {{ ds }} '{{params.src}}/{{ ds }}' '{{params.dst}}' {{params.server}} '{{params.username}}' {{params.password}}",
        params = {
            'src': os.path.join(Variable.get('DATA_DIR'), 'in'),
            'dst': SMB_BASEDIR,
            'server': smb_server,
            'username': smb_username,
            'password': smb_password
        },
        dag=dag
    )

    t_unzip = BashOperator(
        task_id='unzip_task',
        bash_command="python /opt/airflow/dags/roskadastr/un7zip.py '{{params.src}}/{{ ds }}'",
        params = {
            'src': os.path.join(Variable.get('DATA_DIR'), 'in'),
        },
        dag=dag
    )

    t_load = PythonOperator(
        task_id='load_task',
        python_callable=load,
        op_kwargs={
            'folder': os.path.join(Variable.get('DATA_DIR'), 'in'),
            'v_sql_id': SQL_DIR
        }
    )

    t_delete_in = BashOperator(
        task_id='delete_in_files_task',
        bash_command=f"rm -rf {os.path.join(Variable.get('DATA_DIR'), 'in')}/{{{{ ds }}}}/*",
        dag=dag
    )

    t_update = PythonOperator(
        task_id='update_task',
        python_callable=update,
        op_kwargs={
            'v_sql_id': SQL_DIR
        }
    )

    t_export = PythonOperator(
        task_id='export_task',
        python_callable=export,
        op_kwargs={
            'conn_id': CONN_PG_ID,
            'v_sql_id': SQL_DIR,
            'dst_folder': LOCAL_DIR_EXPORT,
        }
    )

    t_copy_export_to_smb = BashOperator(
        task_id='copy_export_to_smb_task',
        bash_command="python /opt/airflow/dags/roskadastr/attachments_tosmb.py {{ds}} '{{params.src}}' '{{params.dst}}' {{params.server}} '{{params.username}}' {{params.password}}",
        params = {
            'src': LOCAL_DIR_EXPORT,
            'dst': SMB_BASEDIR,
            'server': smb_server,
            'username': smb_username,
            'password': smb_password
        },
        dag=dag
    )

    t_delete_export = BashOperator(
        task_id='delete_export_files_task',
        bash_command=f"rm -rf {LOCAL_DIR_EXPORT}/*",
        dag=dag
    )

    t_send_mail = BashOperator(
        task_id='send_mail',
        bash_command="python /opt/airflow/dags/roskadastr/send_request_mail.py '{{params.text}}{{ds}}' '{{params.to}}' '{{params.subject}} {{ds}}' {{params.server}} {{params.email}} '{{params.username}}' {{params.password}}",
        params = {
            'text': '\\\\172.16.0.2\\public\\Управление информационных технологий\\Отдел разработки программного обеспечения\\ежедневка_2023\\',
            'to': Variable.get('EMAIL_EXPORT'),
            'subject': 'ГКО Ежедневка',
            'server': server,
            'email': email,
            'username': username,
            'password': password
        },
        dag=dag
    )

    t_choose_branch = choose_branch(date_start='{{ ds }}', path_to=os.path.join(Variable.get('DATA_DIR'), 'in', '{{ ds }}'))

    start >> t_get_attachments >> t_choose_branch >> t_copy_to_smb >> t_unzip >> t_load >> t_delete_in >> t_update >> t_export >> t_copy_export_to_smb >> t_delete_export >> t_send_mail >> end
