from traceback import extract_tb


def trace_exception(e: Exception, error_type: str = "Error"):
    print(f"\n{error_type}: {e.args}:")
    sf = extract_tb(e.__traceback__)[0]
    print(f"\t{sf.filename}, line {sf.lineno}, in {sf.name}")
    print(f">>\t\t{sf.line}")
