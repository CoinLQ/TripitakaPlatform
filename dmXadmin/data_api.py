from rest_framework.views import APIView
from rest_framework.parsers import BaseParser,FileUploadParser,MultiPartParser
from rest_framework.response import Response
from tdata.models import Tripitaka
import logging
import xlrd
logger = logging.getLogger(__name__)

class PlainTextParser(BaseParser):
    """
    Plain text parser.
    """
    media_type = 'text/plain'

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Simply return a string representing the body of the request.
        """
        content= stream.read()
        print(content)
        print("\n")
        return content

class ImportTripiFromExcel(APIView):
    # parser_classes = (MultiPartParser )

    def post(self, request, format=None):
        file_obj = request.FILES['excel_file'].file
        data =xlrd.open_workbook(file_contents=file_obj.getvalue())
        table = data.sheets()[0]
        tripitakaLst = []
        for i in range(table.nrows):
            row=table.row_values(i)
            code, name, shortname=row[0],row[1],row[2]
            try:
                tripitaka = Tripitaka(code=code, name=name, shortname=shortname)
                tripitaka.save()
                tripitakaLst.append({
                    '藏经':name,
                    'status':'导入成功'
                })
            except Exception as e:
                logger.info(f"tripitaka insert fail:{tripitaka.code}")
                tripitakaLst.append({
                    '藏经': name,
                    'status': '跳过'
                })
        return Response(data=tripitakaLst)

        # tripitakaLst=[]
        # for line in file_obj.readlines():
        #     code, name, shortname = line.decode("utf-8").rstrip().split()
        #     try:
        #         tripitaka = Tripitaka(code=code, name=name, shortname=shortname)
        #         tripitaka.save()
        #         tripitakaLst.append(tripitaka)
        #     except Exception as e:
        #         logger.info(f"tripitaka insert fail:{tripitaka.code}")
        # # do some stuff with uploaded file
        # return Response(data=tripitakaLst)

