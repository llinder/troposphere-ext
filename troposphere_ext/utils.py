import re

def camel_to_snake(value):
    return '_'.join(filter(None, re.split(r'([A-Z][^A-Z]*)', value))).lower()