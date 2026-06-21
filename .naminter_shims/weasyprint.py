class HTML:
    def __init__(self, *a, **k):
        raise RuntimeError("weasyprint unavailable on this platform; PDF export disabled")
    def write_pdf(self, *a, **k):
        raise RuntimeError("weasyprint unavailable on this platform; PDF export disabled")
