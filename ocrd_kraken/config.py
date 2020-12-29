import json
from pkg_resources import resource_filename

with open(resource_filename(__name__, 'ocrd-tool.json'), 'r', encoding='utf-8') as f:
    OCRD_TOOL = json.load(f)
