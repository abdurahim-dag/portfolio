"""Скрипт удаляет элементы Parcel по списку, а так же элементы без детей."""
import logging

import pandas as pd
from lxml import etree as ET


def truncate(el):
    for child in el.findall('*'):
        if child.tag != 'Parcel':
            truncate(child)
    if len(el.findall('*')) == 0:
        parent = el.getparent()
        parent.remove(el)


target_xml = r'D:\Мусорка\cv_3705_2023_05_04_12_57_26\COST\COST_1.xml'
list_cad_nums_file = r'D:\Мусорка\17.04-.xlsx'

cad_nums = []
xlsx = pd.ExcelFile(list_cad_nums_file)
df = pd.read_excel(xlsx, header=None)
for _, row in df.iterrows():
    cad_nums.append(row[0])

with open(target_xml,"r",encoding="utf8") as file_xml:

    tree = ET.parse(file_xml)

    root = tree.getroot()
    parcels = root.findall('*//Parcel')

    if len(parcels) > 0:
        for parcel in parcels:
            cad_num = parcel.attrib['CadastralNumber']
            if cad_num in cad_nums:
                logging.warning('CadastralNumber %s deleted', cad_num)
                parent = parcel.getparent()
                parent.remove(parcel)

    cr = root.find('*//Cadastral_Region')
    truncate(cr)


tree.write('result.xml', encoding='utf-8', xml_declaration=True)
