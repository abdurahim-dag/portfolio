"""Выгрузка из бонусной системы в DWH"""
import logging
import pathlib
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.models.connection import Connection
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import psycopg
import pandas as pd
import numpy
from airflow.models.variable import Variable
import re
import os
import roskadastr.models as models
from roskadastr.storage import WorkflowStorage


args = {
    'owner': 'ragim',
    'email': ['ragimatamov@yandex.ru'],
    'email_on_failure': False,
    'email_on_retry': False,
}

SMB_BASEDIR = Variable.get('SMB_CODES')
LOCAL_DIR_IN = os.path.join(Variable.get('DATA_DIR'), 'codes')
CONN_PG_ID = 'PG_GKO'
SQL_DIR = 'SQL_DIR'

conn = Connection.get_connection_from_secrets('smb_public')
smb_server = conn.host
smb_username = conn.login
smb_password = conn.password


def load(folder: str, v_sql_id: str):
    hook = PostgresHook(CONN_PG_ID)
    uri = hook.get_uri()
    conn: psycopg.Connection
    curs: psycopg.Cursor

    sql_response_code = open(os.path.join(Variable.get(v_sql_id), 'response_code.sql'), encoding='utf8').read()
    sql_check_path = open(os.path.join(Variable.get(v_sql_id), 'check_exists_codepath.sql'), encoding='utf8').read()
    sql_response_code_file = open(os.path.join(Variable.get(v_sql_id), 'response_code_file.sql'), encoding='utf8').read()

    with psycopg.connect(uri) as conn:
        conn.autocommit = False
        with conn.cursor() as curs:
            path = pathlib.Path(folder)

            for fxls in path.glob('*.xlsx'):
                if fxls.is_file() and '~' not in str(fxls.name):
                    fxls_path = str(fxls.absolute())
                    curs.execute(sql_check_path, {'path': fxls_path})
                    if curs.fetchone():
                        continue

                    fname = fxls.name
                    curs.execute(
                        sql_response_code_file,
                        {
                            'file_name': fname,
                            'path': fxls_path,
                            'date': str(pendulum.now().date())
                        },
                    )
                    response_file_id = curs.fetchone()[0]
                    conn.commit()

                    logging.info(f"Started for {fname}")
                    cadnum_col = {
                        'ОКС': 'КАДАСТРОВЫЙ № ОКС',
                        'ЗУ': 'КАД №'
                    }
                    for sheet_name in cadnum_col.keys():
                        df = pd.read_excel(fxls.absolute(), sheet_name=sheet_name, header=None)
                        i = 0
                        for c in df.iloc[:, 1]:
                            if c is not numpy.nan:
                                break
                            i += 1
                        if i == 0:
                            logging.info("Not Find ROW Start Table")

                        cols = []
                        j = 0
                        for c in df.iloc[i]:
                            c = str(c)
                            if c == 'nan':
                                c = 'NaN' + str(j)
                                j += 1
                            if c.upper() not in cols:
                                cols.append(c.upper())
                            else:
                                cols.append(c.upper() + str(j))
                                j += 1
                        df = df.drop(list(range(i+1)))
                        df.columns = cols

                        j = 0
                        col = cadnum_col[sheet_name]

                        for index, row in df.iterrows():
                            if row[col] is not numpy.nan:
                                cad_num = row[col]
                                code = row['КОД']
                                curs.execute(
                                    sql_response_code,
                                    {
                                        'file_id': response_file_id,
                                        'code': code,
                                        'cad_num': cad_num
                                    },
                                )
                                conn.commit()

                            j += 1
                        logging.info(f"Added rows - {j}")


with DAG(
        'response-codes-to-pg-dag',
        catchup=False,
        default_args=args,
        description='Dag for load data from origin bonus system to staging',
        is_paused_upon_creation=True,
        start_date=pendulum.datetime(2022, 5, 5, tz="UTC"),
        schedule_interval='*/15 * * * *',  # Задаем расписание выполнения дага - каждый 15 минут.
        tags=['response', 'codes'],
) as dag:
    start = EmptyOperator(task_id='start')
    end = EmptyOperator(task_id='end')

    t_copy = BashOperator(
        task_id='copy_codes_task',
        bash_command="python /opt/airflow/dags/roskadastr/copy_dir_fromsmb.py '{{params.src}}' '{{params.dst}}' '{{params.server}}' '{{params.username}}' '{{params.password}}'",
        params = {
            'src': SMB_BASEDIR,
            'dst': LOCAL_DIR_IN,
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
            'folder': LOCAL_DIR_IN, 'v_sql_id': SQL_DIR
        }
    )

    t_delete = BashOperator(
        task_id='delete_task',
        bash_command=f"rm -rf {LOCAL_DIR_IN}/*",
        dag=dag
    )

    t_set_response_id = SQLExecuteQueryOperator(
        task_id='set_response_id',
        conn_id=CONN_PG_ID,
        sql="sql/set_response_id_for_code.sql",
        dag=dag
    )

    start >> t_copy >> t_load >> t_delete >> t_set_response_id >> end
