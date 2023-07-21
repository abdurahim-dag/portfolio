import paramiko

# Установка соединения с сервером SFTP
host = '37.140.192.13'
port = 22
username = 'u0354535'
password = 'plHcJ_7Z'

transport = paramiko.Transport((host, port))
transport.connect(username=username, password=password)

# Создание клиента SFTP
sftp = transport.open_sftp()

# Загрузка файла на сервер
local_path = 'local_file.txt'
remote_path = 'remote_directory/remote_file.txt'

sftp.put(local_path, remote_path)

# Закрытие соединения
sftp.close()
transport.close()
