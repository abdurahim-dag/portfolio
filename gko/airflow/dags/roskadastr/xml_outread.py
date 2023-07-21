import logging
import re
import json
import pathlib
import pandas as pd
import numpy
import pendulum
import roskadastr.models as models
import xmltodict


class Reader:

    def __init__(
            self,
            folder: str,
            type_id: int,
            reg_num: str = None
    ):
        self.folder = folder
        self.type_id = type_id
        self.reg_num = reg_num

    def get(self):
        path = pathlib.Path(self.folder)
        for folder in path.iterdir():
            if folder.is_dir():
                reestr_name = folder.name
                file_pdf = self._get_pdf(folder=folder)
                if file_pdf:
                    response_pdf = str(file_pdf.absolute())
                else:
                    response_pdf = ''

                # TODO: Дата возможно должна приходить из airflow
                date = str(pendulum.now().date())
                yield models.Response(
                    response_date=date,
                    response_reg_num=self.reg_num,
                    response_type_id=self.type_id,
                    response_name=reestr_name,
                    response_description=str(folder.absolute()),
                    response_pdf=response_pdf,
                )

                for ods in folder.glob('**/*.ods'):
                    if ods.is_file() and '~' not in str(ods.absolute()):

                        #считываем  и находим строку начала таблицы
                        df_cost_ok = pd.read_excel(ods.absolute(), sheet_name='II', header=None)
                        i = 0
                        for c in df_cost_ok.iloc[:, 1]:
                            if c is not numpy.nan:
                                break
                            i += 1
                        if i == 0:
                            print("Not Find ROW Start Table")
                            break

                        cols = []
                        j = 0
                        for c in df_cost_ok.iloc[i]:
                            c = str(c)
                            if c == 'nan':
                                c = 'NaN' + str(j)
                                j += 1
                            if c.upper() not in cols:
                                cols.append(c.upper())
                            else:
                                cols.append(c.upper() + str(j))
                                j += 1

                        df_cost_ok = df_cost_ok.drop(list(range(i+1)))
                        df_cost_ok.columns = cols
                        count_cost_ok = int(df_cost_ok.count()[0])

                        df_cost_bad = pd.read_excel(ods.absolute(), sheet_name='III', header=None)
                        i = 0
                        for c in df_cost_bad.iloc[:, 1]:
                            if c is not numpy.nan:
                                break
                            i += 1
                        if i == 0:
                            print("Not Find ROW Start Table")
                            break

                        cols = []
                        j = 0
                        for c in df_cost_bad.iloc[i]:
                            c = str(c)
                            if c == 'nan':
                                c = 'NaN' + str(j)
                                j += 1
                            if c.upper() not in cols:
                                cols.append(c.upper())
                            else:
                                cols.append(c.upper() + str(j))
                                j += 1

                        df_cost_bad = df_cost_bad.drop(list(range(i+1)))
                        df_cost_bad.columns = cols
                        count_cost_bad = int(df_cost_bad.count()[0])

                        yield models.ResponseAct(
                            response_act_ods_filename=ods.name,
                            response_act_count_ok=count_cost_ok,
                            response_act_count_bad=count_cost_bad,
                            response_act_ods_path=str(ods.absolute()),
                        )

                # обработка xmls
                for fxml in folder.glob('**/*.xml'):
                    if fxml.is_file():
                        xmltext = open(fxml, 'rb').read()

                        if xmltext[:3] == b'\xef\xbb\xbf':
                            xmltext = xmltext.decode("utf-8-sig")
                        else:
                            xmltext = xmltext.decode("utf-8")

                        xmltext = re.sub(r"\t", "", xmltext)
                        xmltext = re.sub(r"\r", "", xmltext)
                        xmltext = re.sub(r"\n", "", xmltext)

                        xml_to_dict = xmltodict.parse(xmltext)
                        jsn = json.dumps(xml_to_dict, ensure_ascii=False)
                        if fxml.name.startswith('COST'):
                            typez = 'cost'
                        elif fxml.name.startswith('FD'):
                            typez = 'fd'
                        else:
                            raise Exception(f"Unexpected xml type - {fxml.name}")

                        yield models.ResponseFile(
                            response_file_name=fxml.name,
                            response_file_path=str(fxml.absolute()),
                            response_file_content=jsn,
                            response_file_type=typez,
                        )

            else:
                logging.warning(f"Unexpected {str(folder)}")

    @staticmethod
    def _get_pdf(folder: pathlib.Path) -> pathlib.Path:
        for fpdf in folder.glob('**/*.docx'):
            return fpdf
