# controller.py
import os
from marina_office_control.writer import WriterController
from marina_office_control.calc import CalcController
from marina_office_control.impress import ImpressController

class DocumentController:
    def __init__(self):
        self.writer = WriterController()
        self.calc = CalcController()
        self.impress = ImpressController()

    def open(self, filepath: str):
        ext = os.path.splitext(filepath)[1]
        if ext in ['.odt', '.docx', '.txt']:
            return self.writer.load(filepath)
        elif ext in ['.ods', '.xlsx', '.csv']:
            return self.calc.load(filepath)
        elif ext in ['.odp', '.pptx']:
            return self.impress.load(filepath)
        else:
            raise ValueError(f"Unsupported format: {ext}")
