import gostcrypto
import pathlib

def verify_signature(data_file, signature_file, certificate_file):
    # Создание объекта криптографического провайдера
    crypto = gostcrypto.Crypto()

    # Загрузка данных из файла
    with open(data_file, 'rb') as file:
        data = file.read()

    # Загрузка подписи из файла
    with open(signature_file, 'rb') as file:
        signature = file.read()

    # Загрузка сертификата из файла
    with open(certificate_file, 'rb') as file:
        certificate = file.read()

    # Проверка подписи
    result = crypto.verify(data, signature, certificate)

    # Вывод результата проверки
    if result:
        print("Подпись действительна.")
    else:
        print("Подпись недействительна.")

# Путь к файлу с данными (ccc.xml)
data_file = r'C:\Users\Admin\PycharmProjects\gko\utils\sign\test\EGRN_VK_INCCA0001420612_ALS_POM_spisok (ПОМ по списку кад. _)-2645306.xml'

# Путь к файлу с подписью (ccc.xml.sig)
signature_file = r'C:\Users\Admin\PycharmProjects\gko\utils\sign\test\EGRN_VK_INCCA0001420612_ALS_POM_spisok (ПОМ по списку кад. _)-2645306.xml.sig'

cert_dir = r'C:\Users\Admin\PycharmProjects\gko\utils\sign\sert'
for certificate_file in pathlib.Path(cert_dir).glob('*.cer'):
    # Вызов функции для проверки подписи
    verify_signature(data_file, signature_file, certificate_file)
