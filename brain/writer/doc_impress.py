# impress.py
from unotools import connect

class ImpressController:
    def __init__(self):
        self.desktop = connect()
        self.doc = None

    def load(self, filepath):
        self.doc = self.desktop.open_doc(filepath)
        return f"Presentation loaded: {filepath}"

    def add_slide(self, title="New Slide"):
        slides = self.doc.slides
        slide = slides.create_slide()
        slide.title = title

    def save(self, output_path=None):
        if output_path:
            self.doc.save_as(output_path)
        else:
            self.doc.save()

    def close(self):
        self.doc.close()
