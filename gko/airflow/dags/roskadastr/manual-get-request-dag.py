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
from airflow.models import TaskInstance, BaseOperator
import mmap
import json
from airflow.models.variable import Variable
from airflow.models.connection import Connection
from roskadastr.xml_read import Reader
import roskadastr.models as models
import psycopg
import pandas as pd
import xlsxwriter
from airflow.decorators import task

args = {
    'owner': 'ragim',
    'email': ['ragimatamov@yandex.ru'],
    'email_on_failure': False,
    'email_on_retry': False,
}

SMB_DIR = r'/public/Управление информационных технологий/Отдел разработки программного обеспечения/Перечень_2022_xml'
dt = '2022-01-01'
LOCAL_DIR = os.path.join(Variable.get('DATA_DIR'), 'in_manual')
SQL_DIR = 'SQL_DIR'

conn = Connection.get_connection_from_secrets('smb_public')
smb_server = conn.host
smb_username = conn.login
smb_password = conn.password

CONN_PG_ID = 'PG_GKO'


def load(ti: TaskInstance, folder: str, v_sql_id: str):
    folder = pathlib.Path(folder)
    hook = PostgresHook(CONN_PG_ID)
    uri = hook.get_uri()
    conn: psycopg.Connection
    curs: psycopg.Cursor

    sql_request = open(os.path.join(Variable.get(v_sql_id), 'request.sql'), encoding='utf8').read()
    sql_request_file = open(os.path.join(Variable.get(v_sql_id), 'request_file.sql'), encoding='utf8').read()
    sql_rejected = open(os.path.join(Variable.get(v_sql_id), 'rejected.sql'), encoding='utf8').read()

    reader = Reader(
        folder=folder,
        type_id=0,
        reg_num=''
    )
    with psycopg.connect(uri) as conn:
        conn.autocommit = False
        with conn.cursor() as curs:
            for el in reader.get():
                if isinstance(el, models.Request):
                    curs.execute(
                        sql_request,
                        {
                            'date': el.request_date,
                            'reg_num': el.request_reg_num,
                            'type_id': str(el.request_type_id),
                            'name': el.request_name,
                            'descr': el.request_description,
                            'pdf': None
                        },
                    )
                    request_id = curs.fetchone()[0]
                    ti.xcom_push(key='request_id', value=request_id)
                    conn.commit()
                elif isinstance(el, models.RequestFile):
                    try:
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
                    except Exception as e:
                        conn.rollback()
                        logging.info(re.escape(str(e)))
                        curs.execute(
                            sql_rejected,
                            ('gko.request_file', re.escape(str(e)), 'manual request', el.request_file_name, request_id, pendulum.now())
                        )
                        conn.commit()


def update(task: BaseOperator, ti: TaskInstance, v_sql_id: str):
    hook = PostgresHook(CONN_PG_ID)
    uri = hook.get_uri()
    conn: psycopg.Connection
    curs: psycopg.Cursor

    sql_parcel = open(os.path.join(Variable.get(v_sql_id), 'parcel.sql'), encoding='utf8').read()
    sql_rejected = open(os.path.join(Variable.get(v_sql_id), 'rejected.sql'), encoding='utf8').read()
    sql_get_request_file_id = open(os.path.join(Variable.get(v_sql_id), 'get_request_file_by_id.sql'), encoding='utf8').read()

    task_id = task.upstream_list[0].task_id
    request_id = ti.xcom_pull(key='request_id', task_ids=[task_id])[0]

    with psycopg.connect(uri) as conn:
        conn.autocommit = False
        with conn.cursor() as curs:
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
                        (re.escape(str(e)), request_file_id, pendulum.now())
                    )
                    conn.commit()


with DAG(
        'manual-get-request-dag',
        catchup=False,
        default_args=args,
        description='Dag for load requests from smb shared folder to pg',
        is_paused_upon_creation=True,
        start_date=pendulum.datetime(2022, 5, 5, tz="UTC"),
        schedule_interval='@once',
        tags=['request', 'manual'],
) as dag:
    start = EmptyOperator(task_id='start')
    end = EmptyOperator(task_id='end')

    t_copy = BashOperator(
        task_id='copy_responses_task',
        bash_command="python /opt/airflow/dags/roskadastr/copy_fromsmb.py '{{params.src}}' '{{params.dst}}' '{{params.server}}' '{{params.username}}' '{{params.password}}'",
        params = {
            'src': SMB_DIR,
            'dst': LOCAL_DIR,
            'server': smb_server,
            'username': smb_username,
            'password': smb_password
        },
        dag=dag
    )

    t_load = PythonOperator(
        task_id='load_task',
        python_callable=load,
        op_kwargs={
            'folder': LOCAL_DIR,
            'v_sql_id': SQL_DIR
        },
        provide_context=True,
    )

    t_update = PythonOperator(
        task_id='update_task',
        python_callable=update,
        op_kwargs={
            'dt': dt,
            'v_sql_id': SQL_DIR
        },
        provide_context=True,
    )

    t_delete_in = BashOperator(
        task_id='delete_in_files_task',
        bash_command=f"rm -rf {os.path.join(Variable.get('DATA_DIR'), 'in_manual')}/*",
        dag=dag
    )

    start >> t_copy >> t_load >> t_update >> t_delete_in >> end

