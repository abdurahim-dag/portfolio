"""Выгрузка из бонусной системы в DWH"""
import logging
from airflow.models.variable import Variable
import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.models.connection import Connection
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
import psycopg
from roskadastr.xml_outread import Reader
import re
import os
import json
import roskadastr.models as models
from roskadastr.storage import WorkflowStorage

args = {
    'owner': 'ragim',
    'email': ['ragimatamov@yandex.ru'],
    'email_on_failure': False,
    'email_on_retry': False,
}

SMB_BASEDIR = Variable.get('SMB_OUT')
DST_DIR = os.path.join(Variable.get('DATA_DIR'), 'out')
SQL_DIR = 'SQL_DIR'
CONN_PG_ID = 'PG_GKO'

conn = Connection.get_connection_from_secrets('smb_public')
smb_server = conn.host
smb_username = conn.login
smb_password = conn.password


def load(folder: str, v_sql_id: str):
    hook = PostgresHook(CONN_PG_ID)
    uri = hook.get_uri()
    conn: psycopg.Connection
    curs: psycopg.Cursor

    sql_response = open(os.path.join(Variable.get(v_sql_id), 'response.sql'), encoding='utf8').read()
    sql_response_file = open(os.path.join(Variable.get(v_sql_id), 'response_file.sql'), encoding='utf8').read()
    sql_response_act = open(os.path.join(Variable.get(v_sql_id), 'response_act.sql'), encoding='utf8').read()

    reader = Reader(
        folder=folder,
        type_id=16,
        reg_num=''
    )

    with psycopg.connect(uri) as conn:
        conn.autocommit = False
        with conn.cursor() as curs:
            for el in reader.get():
                if isinstance(el, models.Response):
                    if el.response_pdf:
                        file_pdf = open(el.response_pdf, 'rb').read()
                        pdf = psycopg.Binary(file_pdf)
                    else:
                        pdf = ''
                    curs.execute(
                        sql_response,
                        {
                            'date': el.response_date,
                            'reg_num': el.response_reg_num,
                            'type_id': str(el.response_type_id),
                            'name': el.response_name,
                            'descr': el.response_description,
                            'pdf': pdf
                        },
                    )
                    response_id = curs.fetchone()[0]
                    conn.commit()
                elif isinstance(el, models.ResponseFile):
                    content = json.dumps(el.response_file_content, ensure_ascii=False)
                    content = re.sub(r"\t", "", content)
                    content = re.sub(r"\r", "", content)
                    content = re.sub(r"\n", "", content)
                    curs.execute(
                        sql_response_file,
                        {
                            'file_name': el.response_file_name,
                            'path': el.response_file_path,
                            'response_id': str(response_id),
                            'file_type': el.response_file_type,
                            'descr': el.response_file_description,
                            'content': content,
                        }
                    )
                    conn.commit()
                elif isinstance(el, models.ResponseAct):
                    file_pdf = open(el.response_act_ods_path, 'rb').read()
                    pdf = psycopg.Binary(file_pdf)
                    curs.execute(
                        sql_response_act,
                        {
                            'file_name': el.response_act_ods_filename,
                            'count_ok': str(el.response_act_count_ok),
                            'count_bad': str(el.response_act_count_bad),
                            'response_id': str(response_id),
                            'pdf': pdf,
                        }
                    )
                    conn.commit()


def update(conn_pg_id: str, v_sql_id: str):
    hook = PostgresHook(conn_pg_id)
    uri = hook.get_uri()
    conn: psycopg.Connection
    curs: psycopg.Cursor

    sql_response_parcel = open(os.path.join(Variable.get(v_sql_id), 'response_parcel.sql'), encoding='utf8').read()
    sql_rejected = open(os.path.join(Variable.get(v_sql_id), 'rejected.sql'), encoding='utf8').read()
    sql_get_response_id = open(os.path.join(Variable.get(v_sql_id), 'get_response_by_id.sql'), encoding='utf8').read()

    LAST_LOADED_ID_KEY = 'response_id'
    wf_storage = WorkflowStorage(
        conn_id=conn_pg_id, # название соединения в Airflow БД состояния
        etl_key='response', # Ключ идентификации в БД прогресса
        workflow_settings={ # Значение по умолчанию начального состояния прогресса.
            LAST_LOADED_ID_KEY: -1
        },
        schema='gko' # Схема в БД, где хранится состояние
    )
    wf_setting = wf_storage.retrieve_state()
    last_loaded = wf_setting.workflow_settings[LAST_LOADED_ID_KEY]

    with psycopg.connect(uri) as conn:
        conn.autocommit = False
        with conn.cursor() as curs:
            curs.execute(sql_get_response_id, {'response_id': last_loaded})
            response_ids = curs.fetchall()
            response_ids = [r[0] for r in response_ids]
            for response_id in response_ids:
                logging.info('Start update for response_id=%s', response_id)
                try:
                    curs.execute(sql_response_parcel.format(response_id))
                    conn.commit()
                    logging.info("Rows affected: %s", curs.rowcount)
                except Exception as e:
                    conn.rollback()
                    logging.info(re.escape(str(e)))

                    curs.execute(
                        sql_rejected,
                        ('gko.response_parcel', re.escape(str(e)), 'gko.response_file', '', response_id, pendulum.now())
                    )
                    conn.commit()
            if len(response_ids) > 0:
                wf_setting.workflow_settings[LAST_LOADED_ID_KEY] = response_id
                wf_storage.save_state(wf_setting)


with DAG(
        'response-to-pg-dag',
        catchup=False,
        default_args=args,
        description='Dag for load data from origin bonus system to staging',
        is_paused_upon_creation=True,
        start_date=pendulum.datetime(2022, 5, 5, tz="UTC"),
        schedule_interval='*/15 * * * *',  # Задаем расписание выполнения дага - каждый 15 минут.
        tags=['response'],
) as dag:
    start = EmptyOperator(task_id='start')
    end = EmptyOperator(task_id='end')

    t_copy = BashOperator(
        task_id='copy_responses_task',
        bash_command="python /opt/airflow/dags/roskadastr/copy_fromsmb.py '{{params.src}}' '{{params.dst}}' '{{params.server}}' '{{params.username}}' '{{params.password}}'",
        params = {
            'src': SMB_BASEDIR,
            'dst': DST_DIR,
            'server': smb_server,
            'username': smb_username,
            'password': smb_password
        },
        dag=dag
    )

    t_unzip = BashOperator(
        task_id='unzip_task',
        bash_command="python /opt/airflow/dags/roskadastr/un7zip.py '{{params.src}}'",
        params = {
            'src': DST_DIR,
        },
        dag=dag
    )

    t_load = PythonOperator(
        task_id='load_task',
        python_callable=load,
        op_kwargs={
            'folder': DST_DIR,
            'v_sql_id': SQL_DIR
        }
    )

    t_delete = BashOperator(
        task_id='delete_task',
        bash_command=f"rm -rf {DST_DIR}/*",
        dag=dag
    )

    t_update = PythonOperator(
        task_id='update_task',
        python_callable=update,
        op_kwargs={
            'conn_pg_id': CONN_PG_ID, 'v_sql_id': SQL_DIR
        }
    )

    t_set_request_id = SQLExecuteQueryOperator(
        task_id='set_request_id',
        conn_id=CONN_PG_ID,
        #sql=f"{Variable.get('SQL_DIR')}/set_request_id_for_response.sql",
        sql="sql/set_request_id_for_response.sql",
        dag=dag
    )

    start >> t_copy >> t_unzip >> t_load >> t_delete >> t_update >> t_set_request_id >> end
