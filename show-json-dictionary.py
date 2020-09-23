import json
import pprint

with open('dict2.json', 'r') as infile:
    words = json.load(infile)
    pprint.pprint(words)
