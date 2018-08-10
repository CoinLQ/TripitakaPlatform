from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.parsers import BaseParser, FileUploadParser, MultiPartParser
from rest_framework.response import Response
from tsdata.models import * 
from dmXadmin.import_sutra import ImportSutraFromExcel
import logging
import xlrd
import xlwt
from datetime import datetime
from django.conf import settings

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
        content = stream.read()
        print(content)
        print("\n")
        return content


def write_row(result_sheet, row_index, cell_values):
    for i in range(len(cell_values)):
        result_sheet.write(row_index, i, cell_values[i])


class ImportTripiFromExcel(APIView):
    # parser_classes = (MultiPartParser )

    def post(self, request, format=None):
        try:
            file_obj = request.FILES['excel_file'].file
            data =xlrd.open_workbook(file_contents=file_obj.getvalue())
            table = data.sheets()[0]
            #读第一行，确定 实体藏编号、实体藏名称、实体藏简称 的位置
            code_index, name_index, shortname_index, remark_index = self.getColIndexes(table.row_values(0))
            if code_index < 0 or name_index < 0 or shortname_index < 0:
                # Unprocessable Entity
                return Response(status=422)

            result_file = xlwt.Workbook()
            result_sheet = result_file.add_sheet("实体藏导入结果", True)
            write_row(result_sheet, 0, ['编码', '藏名', '简称', '备注', '导入结果'])

            for i in range(1, table.nrows):
                row = table.row_values(i)
                code, name, shortname=row[code_index], row[name_index], row[shortname_index]
                remark = row[remark_index] if remark_index >= 0 else ''
                try:
                    tripitaka = Tripitaka(code=code, name=name, shortname=shortname, remark=remark,creator=request._user)
                    tripitaka.save()
                    write_row(result_sheet, i, [code, name, shortname, remark, '成功'])
                except Exception as e:
                    logger.info(f"tripitaka insert fail:{tripitaka.code}")
                    write_row(result_sheet, i, [code, name, shortname, remark, '失败'])
            r_file_name = f"实体藏导入结果{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.xlsx"
            result_file.save(f"{settings.EXCEL_DIR}/{r_file_name}")
            return Response(status=200, data={
                'status': 0, 'result_file_name': r_file_name
            })
        except Exception as e:
            return Response(status=200, data={
                'status': -1, 'msg': str(e)})
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

    def getColIndexes(self, first_row):
        code_index, name_index, shortname_index, remark_index = -1, -1, -1, -1
        for cellIndex in range(len(first_row)):
            cell = first_row[cellIndex]
            if cell == '编码':
                code_index = cellIndex
            elif cell == '藏名':
                name_index = cellIndex
            elif cell == '简称':
                shortname_index = cellIndex
            elif cell == '备注':
                remark_index = cellIndex
        return code_index, name_index, shortname_index, remark_index


class ImportVolFromExcel(APIView):
    # parser_classes = (MultiPartParser )

    def post(self, request, format=None):
        file_obj = request.FILES['excel_file'].file
        data = xlrd.open_workbook(file_contents=file_obj.getvalue())
        table = data.sheets()[0]
        volumeLst = []
        # 读第一行，确定 实体藏编号、实体藏名称、实体藏简称 的位置
        tripitaka_code_index, vol_no_index, total_pages_index, cur_pages_index, remark_index = self.getColIndexes(table.row_values(0))
        if vol_no_index < 0 or total_pages_index < 0 or cur_pages_index < 0:
            # Unprocessable Entity
            return Response(status=422)

        result_file = xlwt.Workbook()
        result_sheet = result_file.add_sheet("实体册导入结果", True)
        write_row(result_sheet, 0, ['藏经编码', '册序号', '册页数', '实际页数', '备注', '导入结果'])

        for i in range(1, table.nrows):
            row = table.row_values(i)
            t_code = row[tripitaka_code_index]
            tripitaka = Tripitaka.objects.get(code=t_code)
            vol_no, total_pages, cur_pages = row[vol_no_index], row[total_pages_index], row[cur_pages_index]
            remark = row[remark_index] if remark_index >= 0 else ''
            try:
                volume = Volume(tripitaka=tripitaka, vol_no=vol_no, total_pages=total_pages, cur_pages=cur_pages, remark=remark, creator=request._user)
                volume.save()
                volumeLst.append({
                    '册': t_code+str(vol_no),
                    'status': '导入成功'
                })
                write_row(result_sheet, i, [t_code, vol_no, total_pages, cur_pages, remark, '成功'])
            except Exception as e:
                logger.info(f"volume insert fail:{t_code+str(vol_no)+str(e)}")
                volumeLst.append({
                    '册': t_code+str(vol_no),
                    'status': '跳过'
                })
                write_row(result_sheet, i, [t_code, vol_no, total_pages, cur_pages, remark, '失败'])
        r_file_name = f"实体册导入结果{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.xlsx"
        result_file.save(f"{settings.EXCEL_DIR}/{r_file_name}")
        return Response(status=200, data={
            'status':0,
            'result_file_name': r_file_name
        })

    def getColIndexes(self, first_row):
        tripitaka_code_index, vol_no_index, total_pages_index, cur_pages_index, remark_index = -1, -1, -1, -1, -1
        for cellIndex in range(len(first_row)):
            cell = first_row[cellIndex].strip(' ')
            if cell == '藏经编码':
                tripitaka_code_index = cellIndex
            elif cell == '册序号':
                vol_no_index = cellIndex
            elif cell == '册页数':
                total_pages_index = cellIndex
            elif cell == '实际页数':
                cur_pages_index = cellIndex
            elif cell == '备注':
                remark_index = cellIndex

        return tripitaka_code_index, vol_no_index, total_pages_index, cur_pages_index, remark_index
