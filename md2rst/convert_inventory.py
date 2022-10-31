import sys
import os
import json
from sphinx.util.inventory import InventoryFile


def convert_inventory(input_path):
    with open(input_path, 'rb') as f:
        invdata = InventoryFile.load(f, '', os.path.join)

    refs = invdata['std:label']
    labels = {}
    for ref, info in refs.items():
        if ':' not in ref:
            continue
        doc, label = ref.split(':', 1)
        htmlref = info[2].split('#', 1)[1]
        labels.setdefault(doc, {})[htmlref] = label
    return labels


def main():
    if len(sys.argv) < 2:
        print("Usage: convert_inventory.py _build/objects.inv output.json")
        return 2
    labels = convert_inventory(sys.argv[1])

    j = json.dumps(labels)

    if len(sys.argv) > 2:
        with open(sys.argv[2], 'w') as f:
            f.write(j)
    else:
        print(j)

if __name__ == '__main__':
    sys.exit(main())