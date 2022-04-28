import json # import json module
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--vocab_path", type=str)
parser.add_argument("--vocab_file", type=str)

args = parser.parse_args()

vocab_path = args.vocab_path
vocab_file = args.vocab_file
f = open(vocab_file,'w',encoding='utf-8')
with open(vocab_path) as json_file:
    json_data = json.load(json_file)
    for item in json_data["model"]["vocab"].keys():
        f.write(item+'\n')

    f.close()