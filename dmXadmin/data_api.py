from rest_framework.views import APIView
from rest_framework.parsers import BaseParser,FileUploadParser,MultiPartParser
from rest_framework.response import Response

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
        print(str(file_obj.getvalue()))
        # do some stuff with uploaded file
        return Response(status=204)

