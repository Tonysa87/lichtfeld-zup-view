class Operator:
    label=""; description=""; options=set()
    def __init__(self): pass
    @classmethod
    def _class_id(cls): return f"{cls.__module__}.{cls.__qualname__}"
