from rest_framework.views import APIView
from tsdata.models import LQSutra
from dmXadmin.bgtask import create_lqreels_for_lqsutras
from rest_framework.response import Response
import xlrd
import xlwt
from dmXadmin.data_api import write_row
from django.conf import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

COL_SID = '龙泉经编码'
COL_NAME = '实体经名'
COL_AUTHOR = '译者'
COL_TOTAL_REELS = '总卷数'
COL_CUR_REELS = '现有卷数'
COL_REMARK = '备注'


def get_or_default(row_values, index, default):
    return row_values[index] if 0 <= index <= len(row_values) else default


def getint_or_default(row_values, index, default):
    if 0 <= index <= len(row_values):
        try:
            return int(row_values[index])
        except:
            return default
    else:
        return default


class ImportLQSutraFromExcel(APIView):

    def post(self, request, format=None):
        file_obj = request.FILES['excel_file'].file
        workbook = xlrd.open_workbook(file_contents=file_obj.getvalue())
        return self.import_lqsutra(workbook, request._user)

    def import_lqsutra(self, workbook, user):
        new_lqsutra_list = []
        try:
            table = workbook.sheets()[0]
            nrows = table.nrows

            sid_index, name_index, author_index, treels_index, creels_index, remark_index = ImportLQSutraFromExcel.get_col_indexes(
                table.row_values(0))
            if sid_index < 0:
                return Response(data={
                    'status': -1, 'msg': f"缺少{COL_SID}字段"})

            # 创建结果文件
            result_file = xlwt.Workbook()
            result_sheet = result_file.add_sheet("龙泉经导入结果", True)
            write_row(result_sheet, 0,
                      [COL_SID, COL_NAME, COL_AUTHOR, COL_TOTAL_REELS, COL_CUR_REELS, COL_REMARK, '导入结果'])

            # 解析属性
            for i in range(1, nrows):
                row = table.row_values(i)
                sid = row[sid_index].strip()
                code = sid[2:7]
                variant_code = sid[7]
                name = get_or_default(row, name_index, '')
                author = get_or_default(row, author_index, '')
                treels = getint_or_default(row, treels_index, 0)
                creels = getint_or_default(row, creels_index, 0)
                remark = get_or_default(row, remark_index, '')
                try:
                    lqsutra = LQSutra(sid=sid, code=code, variant_code=variant_code,
                                      name=name, author=author,
                                      total_reels=treels, cur_reels=creels,
                                      remark=remark, creator=user)
                    lqsutra.save()
                    write_row(result_sheet, i, [sid, name, author, treels, creels, remark, '成功'])
                    new_lqsutra_list.append(lqsutra)
                    logger.info(f"event=insert-new-lqsutra v={lqsutra}")
                except:
                    write_row(result_sheet, i, [sid, name, author, treels, creels, remark, '跳过'])

            r_file_name = f"龙泉经导入结果{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.xlsx"
            result_file.save(f"{settings.EXCEL_DIR}/{r_file_name}")
            create_lqreels_for_lqsutras([x.sid for x in new_lqsutra_list])
            return Response(status=200, data={
                'status': 0, 'result_file_name': r_file_name
            })
        except Exception as e:
            create_lqreels_for_lqsutras([x.sid for x in new_lqsutra_list])
            logger.error(str(e), exec_info=True)
            return Response(status=200, data={
                'status': -1, 'msg': str(e)
            })

    @staticmethod
    def get_col_indexes(first_row):
        sid_index, name_index, author_index, treels_index, creels_index, remark_index = -1, -1, -1, -1, -1, -1
        for cellIndex in range(len(first_row)):
            cell = first_row[cellIndex]
            if cell == COL_SID:
                sid_index = cellIndex
            elif cell == COL_NAME:
                name_index = cellIndex
            elif cell == COL_AUTHOR:
                author_index = cellIndex
            elif cell == COL_REMARK:
                remark_index = cellIndex
            elif cell == COL_TOTAL_REELS:
                treels_index = cellIndex
            elif cell == COL_CUR_REELS:
                creels_index = cellIndex
        return sid_index, name_index, author_index, treels_index, creels_index, remark_index
