from pyexpat.errors import codes
from turtle import position
import javalang
import json
from pyparsing import null_debug_action
from tqdm import tqdm
import collections
import sys


def get_name(obj):
    if(type(obj).__name__ in ['list', 'tuple']):
        a = []
        for i in obj:
            a.append(get_name(i))
        return a
    elif(type(obj).__name__ in ['dict', 'OrderedDict']):
        a = {}
        for k in obj:
            a[k] = get_name(obj[k])
        return a
    elif(type(obj).__name__ not in ['int', 'float', 'str', 'bool']):
        return type(obj).__name__
    else:
        return obj


def process_source(file_name, save_file):
    with open(file_name, 'r', encoding='utf-8') as source:
        lines = source.readlines()
    with open(save_file, 'w+', encoding='utf-8') as save:
        for line in lines:
            code = line.strip()
            tokens = list(javalang.tokenizer.tokenize(code))
            tks = []
            for tk in tokens:
                if tk.__class__.__name__ == 'String' or tk.__class__.__name__ == 'Character':
                    tks.append('STR_')
                elif 'Integer' in tk.__class__.__name__ or 'FloatingPoint' in tk.__class__.__name__:
                    tks.append('NUM_')
                elif tk.__class__.__name__ == 'Boolean':
                    tks.append('BOOL_')
                else:
                    tks.append(tk.value)
            save.write(" ".join(tks) + '\n')

# Get node type, value, position for code information.
# This is not AST result.
# {"type": "MethodDeclaration", "value": "isTokenExpired", "position": [1, 15]}
def get_flatten_node(file_name, w):
    with open(file_name, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    with open(w, 'w+', encoding='utf-8') as wf:
        for line in tqdm(lines):
            code = line.strip()
            tokens = javalang.tokenizer.tokenize(code)
            token_list = list(javalang.tokenizer.tokenize(code))
            length = len(token_list)
            parser = javalang.parser.Parser(tokens)
            try:
                tree = parser.parse_member_declaration()
            except (javalang.parser.JavaSyntaxError, IndexError, StopIteration, TypeError):
                print(code)
                continue
            flatten = []
            for path, node in tree:
                flatten.append({'path': path, 'node': node})
            
            ign = False
            outputs = []

            for i, Node in enumerate(flatten):
                d = {}
                path = Node['path']
                node = Node['node']
                
                d['id'] = i
                if hasattr(node, 'name'):
                    d['type'] = get_name(node)
                if hasattr(node, 'name'):
                    d['value'] = node.name
                if hasattr(node, 'position'):
                    d['position'] = node.position

                outputs.append(d)
            if not ign:
                wf.write(json.dumps(outputs))
                wf.write('\n')

# Get token list for code information.
# This is not AST result.
# It shows position, code type, code sequence.
# {'type': 'Modifier', 'value': 'static', 'position': '1'}
def get_codeseqsbt(file_name, w):
    with open(file_name, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    with open(w, 'w+', encoding='utf-8') as wf:
        for line in tqdm(lines):
            code = line.strip()
            tokens = javalang.tokenizer.tokenize(code)
            token_list = list(javalang.tokenizer.tokenize(code))
            length = len(token_list)
            codeseq = []
            for i in range(length):
                d = {}
                tmp = str(token_list[i]).split(', ')
                if i == 0:
                    d['type'], d['value'] = tmp[0].split(' ')[0:2]
                    d['value'] = d['value'].replace('"', '')
                    d['position'] = "None"
                    codeseq.append(d)
                else:
                    d['type'], d['value'] = tmp[0].split(' ')[0:2]
                    d['position'] = str(token_list[i-1]).split(', ')[1].split(' ')[1]
                    d['value'] = d['value'].replace('"', '')
                    codeseq.append(d)
                    i += 2
            wf.write(json.dumps(codeseq))
            wf.write('\n')

# codeseq 데이터에서 type 종류 확인
# {'Modifier': 1, 'Identifier': 1, 'Separator': 1, 'Operator': 1, 
# 'Keyword': 1, 'BasicType': 1, 'Null': 1, 'Annotation': 1}
def check_type(codseq_file):
    with open(codseq_file, 'r') as codeseq:
        dict_type = {}
    code = codeseq.readlines()
    for i in tqdm(code):
        c = json.loads(i)
        for i in c:
            if i['type'] not in dict_type:
                dict_type[i['type']] = 1
            else:
                continue
    print(dict_type)



# Get code sequence sbt file (for Model 2)
# This is neither traditional sbt nor sim sbt.
# Because we make sbt file considering code sequence.
# Code: public static boolean isTokenExpired ...
# Traiditonal SBT: ( MethodDeclaration isTokenExpired ( BasicType boolean ) BasicType ...
# sim SBT: MethodDeclaration is token expired BasicType boolean FormalParameter token expiry ...
# code sequequence: public Modifier static Modifier boolean BasicType MethodDeclaration isTokenExpired ...
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

if __name__ == '__main__':
    # pre-process the source code: strings -> STR_, numbers-> NUM_, Booleans-> BOOL_
    process_source(sys.argv[1], 'source.code')
    get_flatten_node('source.code', sys.argv[2])
    get_codeseqsbt('source.code', sys.argv[3])
    codeseq_newsbt('valid.flatten', 'valid.codeseq', 'valid.result')
    # codeseq_newsbt('idflatten', 'idcodeseq', 'idresult')

# python getdata_codeseqsbt.py code flatten codeseq