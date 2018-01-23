
class OCRLine(object):
    '''
    表示OCR识别结果中一个列
    '''
    def __init__(self, x1, y1, x2, y2, x3, y3, x4, y4):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.x3 = x3
        self.y3 = y3
        self.x4 = x4
        self.y4 = y4

    def area(self):
        h = self.y2 - self.y1
        w = self.x2 - self.x3
        return w * h

    @classmethod
    def is_duplicate_line(cls, ocrline1, ocrline2):
        '''
        判断是否是重复的列
        '''
        overlap_region = OCRLine(
            min(ocrline1.x1, ocrline2.x1),
            max(ocrline1.y1, ocrline2.y1),
            min(ocrline1.x2, ocrline2.x2),
            min(ocrline1.y2, ocrline2.y2),
            max(ocrline1.x3, ocrline2.x3),
            min(ocrline1.y3, ocrline2.y3),
            max(ocrline1.x4, ocrline2.x4),
            max(ocrline1.y4, ocrline2.y4)
        )
        ratio1 = overlap_region.area() / ocrline1.area()
        ratio2 = overlap_region.area() / ocrline1.area()
        if (ratio1 > 0.9 and ratio2 > 0.9):
            return True
        return False
