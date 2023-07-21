start: start-airflow start-gko add-conn-pg add-conn-smb add-conn-exchange add-variables

start-airflow:
	cd ./airflow && docker compose up -d --no-deps --build

start-gko:
	PG_PASSWORD=${PG_PASSWORD} docker compose up -d --no-deps --build

add-conn-pg:
	docker exec airflow-webserver bash -c "airflow connections add \"PG_GKO\" --conn-json '{\
    \"conn_type\": \"postgres\",\
    \"login\": \"gko\",\
    \"password\": \"${PG_PASSWORD}\",\
    \"host\": \"172.16.0.30\",\
    \"port\": \"55432\",\
    \"schema\": \"gko\",\
    \"extra\": {\"sslmode\": \"disable\"}\
}'"

add-conn-smb:
	docker exec airflow-webserver bash -c "airflow connections add \"smb_public\" --conn-json '{\
    \"conn_type\": \"samba\",\
    \"login\": \"dagbti\\\atamovrb\",\
    \"password\": \"${SMB_PASSWORD}\",\
    \"host\": \"172.16.0.2\"\
}'"

add-conn-exchange:
	docker exec airflow-webserver bash -c "airflow connections add \"email_exchange\" --conn-json '{\
    \"conn_type\": \"email\",\
    \"schema\": \"rosreestrin@dagbti.ru\",\
    \"login\": \"dagbti\\\rosreestrin\",\
    \"password\": \"${EWS_PASSWORD}\",\
    \"host\": \"mail.dagbti.ru\"\
}'"


add-variables:
	docker cp variables.json airflow-webserver:/data/variables.json
	docker exec airflow-webserver bash -c "airflow variables import /data/variables.json"


stop-airflow:
	cd ./airflow && docker compose down -v

stop-gko:
	docker compose down -v
