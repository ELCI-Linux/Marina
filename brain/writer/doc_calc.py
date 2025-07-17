# calc.py
from unotools import connect

class CalcController:
    def __init__(self):
        self.desktop = connect()
        self.doc = None

    def load(self, filepath):
        self.doc = self.desktop.open_doc(filepath)
        return f"Spreadsheet loaded: {filepath}"

    def write_cell(self, sheet_index, cell, value):
        sheet = self.doc.sheets[sheet_index]
        sheet[cell].value = value

    def read_cell(self, sheet_index, cell):
        sheet = self.doc.sheets[sheet_index]
        return sheet[cell].value

    def save(self, output_path=None):
        if output_path:
            self.doc.save_as(output_path)
        else:
            self.doc.save()

    def close(self):
        self.doc.close()
