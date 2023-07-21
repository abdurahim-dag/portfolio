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
        try:
            date = re.search('.*?(\d\d\d\d-\d\d-\d\d).*', path.name).group(1)
        except:
            date = pendulum.now().strftime('%Y-%m-%d')

        if path.is_dir():
            reestr_name = path.name
            if self.type_id == 16:
                file_pdf = str(self._get_pdf(folder=path).absolute())
            else:
                file_pdf = ''
            yield models.Request(
                request_date=date,
                request_reg_num=self.reg_num,
                request_type_id=self.type_id,
                request_name=reestr_name,
                request_description=str(path.absolute()),
                request_pdf=file_pdf,
            )

            # Deprecate
            # for fxls in folder.glob('**/*.xlsx'):
            #     if fxls.is_file() and '~' not in str(fxls.name):
            #         df_xls = pd.read_excel(fxls.absolute(), header=None, engine='openpyxl', dtype=str)
            #
            #         i = 0
            #         options = []
            #         for c in df_xls.iloc[:, 1]:
            #             if c is not numpy.nan:
            #                 break
            #             options.append(df_xls.iloc[i, 0])
            #             i += 1
            #         options = '|'.join(str(e) for e in options)
            #
            #         cols = []
            #         j = 0
            #         for c in df_xls.iloc[i]:
            #             c = str(c)
            #             if c == 'nan':
            #                 c = 'NaN' + str(j)
            #                 j += 1
            #             if c.upper() not in cols:
            #                 cols.append(c.upper())
            #             else:
            #                 cols.append(c.upper() + str(j))
            #                 j += 1
            #         df_xls = df_xls.drop(list(range(i+1)))
            #         df_xls.columns = cols
            #
            #         jsn = df_xls.to_json(orient="records", force_ascii=False)
            #         logging.info(jsn)
            #
            #         yield models.RequestFile(
            #             request_file_name=fxls.name,
            #             request_file_path=str(fxls.absolute()),
            #             request_file_content=jsn,
            #             request_file_options=f"\"value\": {options}",
            #         )

            for fxml in path.glob('**/*.xml'):
                if fxml.is_file():
                    logging.warning('Load xml %s', fxml.name)
                    xmltext = open(fxml, 'rb').read()

                    if xmltext[:3] == b'\xef\xbb\xbf':
                        xmltext = xmltext.decode("utf-8-sig")
                    else:
                        xmltext = xmltext.decode("utf-8")

                    xmltext = re.sub(r"\t", "", xmltext)
                    xmltext = re.sub(r"\r", "", xmltext)
                    xmltext = re.sub(r"\n", "", xmltext)

                    xml_to_dict = xmltodict.parse(xmltext)

                    options = json.dumps(xml_to_dict['ListForRating']['ListInfo'], ensure_ascii=False)
                    jsn = json.dumps(xml_to_dict, ensure_ascii=False)

                    yield models.RequestFile(
                        request_file_name=fxml.name,
                        request_file_path=str(fxml.absolute()),
                        request_file_content=jsn,
                        request_file_options=options,
                    )

        else:
            logging.warning(f"Unexpected {str(path)}")


    @staticmethod
    def _get_pdf(folder: pathlib.Path) -> pathlib.Path:
        for fpdf in folder.glob('**/*.pdf'):
            return fpdf
        for fpdf in folder.glob('**/*.png'):
            return fpdf

