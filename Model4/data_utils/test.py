from pyexpat.errors import codes
from turtle import position
import javalang
import json
from pyparsing import null_debug_action
from tqdm import tqdm
import collections
import sys

def codeseq_newsbt(flatten, codeseq, w):
    with open(codeseq, 'r') as cs:
        codeseqs = cs.readlines()
        with open(flatten, 'r') as fl:
            flattens = fl.readlines()
            with open(w, 'w+') as wf:
                for c in tqdm(range(len(codeseqs))):
                    result = []
                    # ids = []
                    c_json = json.loads(codeseqs[c])
                    # print(c_json[0])
                    # {'type': 'Modifier', 'value': 'public', 'position': 'None'}
                    for i in c_json:
                        # flatten의 c번째 줄 데이터 load
                        f_json = json.loads(flattens[c])
                        if i['type'] == 'Modifier' or i['type'] == 'Annotation' or i['type'] == 'Null' or i['type'] == 'Keyword' or i['type'] == 'Operator' or i['type'] == 'Separator':
                            tmp = i['value'] + ' ' + i['type']
                            # ids.append('None')
                            result.append(tmp.replace('"', ''))
                        elif i['type'] == 'BasicType':
                            for j in f_json:
                                if 'type' in j:
                                    if j['type'] == 'BasicType' and i['value'] == j['value']:
                                        tmp = i['value'] + ' ' + i['type']
                                        # ids.append(j['id'])
                                        break
                                    else:
                                        continue
                                else:
                                    continue
                            result.append(tmp.replace('"', ''))
                        elif i['type'] == 'Identifier':
                            for j in f_json:
                                if 'value' in j:
                                    if i['value'] == j['value']:
                                        tmp = j['value'] + ' ' + j['type']
                                        result.append(tmp.replace('"', ''))
                                        # ids.append(j['id'])
                                        break
                                    else:
                                        if j == len(f_json):
                                            tmp = i['value'] + ' ' + i['type']
                                            result.append(tmp.replace('"', ''))
                                            # ids.append('None')
                                            break
                                        else:
                                            continue
                                else:
                                    if 'position' in j and j['position'] != None:
                                        if i['position'] == j['position'][1]:
                                            tmp = i['value'] + ' ' + i['type']
                                            result.append(tmp.replace('"', ''))
                                            # ids.append(j['id'])
                                            break
                                        else:
                                            if j == len(f_json):
                                                tmp = i['value'] + ' ' + i['type']
                                                result.append(tmp.replace('"', ''))
                                                # ids.append('None')
                                                break
                                            else:
                                                continue
                                    else:
                                        tmp = i['value'] + ' ' + i['type']
                                        result.append(tmp.replace('"', ''))
                                        # ids.append('None')
                                        break
                    result = ' '.join(result).replace('"', '')
                    # print(ids)
                    wf.write(result)
                    wf.write('\n')

codeseq_newsbt('idflatten', 'idcodeseq', 'idresult')
