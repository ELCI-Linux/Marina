# writer.py
from unotools import connect, LoDocument

class WriterController:
    def __init__(self):
        self.desktop = connect()
        self.doc = None

    def load(self, filepath):
        self.doc = self.desktop.open_doc(filepath)
        return f"Loaded: {filepath}"

    def insert_text(self, text, position=0):
        cursor = self.doc.text.createTextCursor()
        self.doc.text.insertString(cursor, text, False)

    def save(self, output_path=None):
        if output_path:
            self.doc.save_as(output_path)
        else:
            self.doc.save()

    def close(self):
        self.doc.close()
