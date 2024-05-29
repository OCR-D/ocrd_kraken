import json
from ocrd_utils import resource_filename

with open(resource_filename('ocrd_kraken', 'ocrd-tool.json'), 'r', encoding='utf-8') as f:
    OCRD_TOOL = json.load(f)
