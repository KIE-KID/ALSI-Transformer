import collections
import json
import re

import javalang


COMMENT_RX = re.compile("(?<!:)\\/\\/.*|\\/\\*(\\s|.)*?\\*\\/", re.MULTILINE)
#SPACE_RX = re.compile('[\n\r$\s]+', re.MULTILINE)

def process_source(code):
    code = code.replace('\n',' ').strip()
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
    return " ".join(tks)


def get_ast(processed_code):
    code = processed_code.strip()
    tokens = javalang.tokenizer.tokenize(code)
    token_list = list(javalang.tokenizer.tokenize(code))
    length = len(token_list)
    parser = javalang.parser.Parser(tokens)
    try:
        tree = parser.parse_member_declaration()
    except (javalang.parser.JavaSyntaxError, IndexError, StopIteration, TypeError):
        print(code)
    flatten = []
    for path, node in tree:
        flatten.append({'path': path, 'node': node})
    ign = False
    outputs = []
    stop = False
    for i, Node in enumerate(flatten):
        d = collections.OrderedDict()
        path = Node['path']
        node = Node['node']
        children = []
        for child in node.children:
            child_path = None
            if isinstance(child, javalang.ast.Node):
                child_path = path + tuple((node,))
                for j in range(i + 1, len(flatten)):
                    if child_path == flatten[j]['path'] and child == flatten[j]['node']:
                        children.append(j)
            if isinstance(child, list) and child:
                child_path = path + (node, child)
                for j in range(i + 1, len(flatten)):
                    if child_path == flatten[j]['path']:
                        children.append(j)
        d["id"] = i
        n = str(node)
        n = n[:n.find('(')]
        d["type"] = n
        if children:
            d["children"] = children
        value = None
        if hasattr(node, 'name'):
            value = node.name
        elif hasattr(node, 'value'):
            value = node.value
        elif hasattr(node, 'position') and node.position:
            for i, token in enumerate(token_list):
                if node.position == token.position:
                    pos = i + 1
                    value = str(token.value)
                    while (pos < length and token_list[pos].value == '.'):
                        value = value + '.' + token_list[pos + 1].value
                        pos += 2
                    break
        elif type(node) is javalang.tree.This \
                or type(node) is javalang.tree.ExplicitConstructorInvocation:
            value = 'this'
        elif type(node) is javalang.tree.BreakStatement:
            value = 'break'
        elif type(node) is javalang.tree.ContinueStatement:
            value = 'continue'
        elif type(node) is javalang.tree.TypeArgument:
            value = str(node.pattern_type)
        elif type(node) is javalang.tree.SuperMethodInvocation \
                or type(node) is javalang.tree.SuperMemberReference:
            value = 'super.' + str(node.member)
        elif type(node) is javalang.tree.Statement \
                or type(node) is javalang.tree.BlockStatement \
                or type(node) is javalang.tree.ForControl \
                or type(node) is javalang.tree.ArrayInitializer \
                or type(node) is javalang.tree.SwitchStatementCase:
            value = 'None'
        elif type(node) is javalang.tree.VoidClassReference:
            value = 'void.class'
        elif type(node) is javalang.tree.SuperConstructorInvocation:
            value = 'super'

        if value is not None and type(value) is type('str'):
            d['value'] = value
        if not children and not value:
            # print('Leaf has no value!')
            print(type(node))
            print(code)
            ign = True
            # break
        outputs.append(d)
    if not ign:
        return json.dumps(outputs)

def AST_(cur_root_id, node_list):
    cur_root = node_list[cur_root_id]
    list = []
    tmp_dict = {}
    tmp_dict['id'] = cur_root['id']
    tmp_dict['type'] = cur_root['type']

    if 'children' in cur_root:
        chs = cur_root['children']
        temp_list = []
        for ch in chs:
            temp_list.append(AST_(ch, node_list))
        tmp_dict['children'] = temp_list
    if 'value' in cur_root:
        tmp_dict['name'] = cur_root['value']
        return tmp_dict
    list.append(tmp_dict)
    return list

def get_ast_structure(ast):
    ast = json.loads(ast)
    ast = AST_(0, ast)
    return ast








# ISBTCODE 
def ISBTCODE_(cur_root_id, node_list):
    cur_root = node_list[cur_root_id]
    tmp_list = []
    # tmp_list.append("(")

    str = cur_root['type']
    tmp_list.append(str)
    
    if 'children' in cur_root:
        chs = cur_root['children']
        for ch in chs:
            tmp_list.extend(ISBTCODE_(ch, node_list))
    # tmp_list.append(")")
    # tmp_list.append(str)
    '''추가한 코드'''
    if 'value' in cur_root: # 토큰 값 가져오기
        str2 = cur_root['value']
        # str2 = ' '.join([hump2underline(i) for i in str2.split()])
        tmp_list.append(str2) # Camelcase 처리 X
    '''추가한 코드'''

    return tmp_list

def get_isbtcode_structure(ast):
    ast = json.loads(ast)
    ast_sbt = ISBT_(0, ast)
    return ' '.join(ast_sbt)   
    

# IDS
def IDS_(cur_root_id, node_list):
    cur_root = node_list[cur_root_id]
    tmp_list = []
    # tmp_list.append("(")

    str = cur_root['id']
    #str = cur_root['type']
    tmp_list.append(str) # 숫자 1

    if 'children' in cur_root:
        chs = cur_root['children']
        for ch in chs:
            tmp_list.extend(IDS_(ch, node_list))
    # tmp_list.append(")")
    tmp_list.append(str) # 숫자 2

    return tmp_list

def get_ids_structure(ast):
    ast = json.loads(ast)
    ast_sbt = IDS_(0, ast)
    return ' '.join(map(str, ast_sbt))	







# SIMSBTCODE
def SIMSBTCODE_(cur_root_id, node_list):
    cur_root = node_list[cur_root_id]
    tmp_list = []
    # tmp_list.append("(")

    str = cur_root['type']
    tmp_list.append(str)
    
    if 'children' in cur_root:
        chs = cur_root['children']
        for ch in chs:
            tmp_list.extend(SIMSBTCODE_(ch, node_list))
    # tmp_list.append(")")
    # tmp_list.append(str)
    '''추가한 코드'''
    if 'value' in cur_root: # 토큰 값 가져오기
        str2 = cur_root['value']
        str2 = ' '.join([hump2underline(i) for i in str2.split()])
        tmp_list.append(str2)
    '''추가한 코드'''

    return tmp_list

def get_simsbtcode_structure(ast):
    ast = json.loads(ast)
    ast_sbt = SIMSBTCODE_(0, ast)
    return ' '.join(ast_sbt)   

# SIM_IDS
def SIM_IDS_(cur_root_id, node_list):
    cur_root = node_list[cur_root_id]
    tmp_list = []
    # tmp_list.append("(")
    str = cur_root['id'] # 숫자 1
    #str = cur_root['type']
    tmp_list.append(str)

    if 'children' in cur_root:
        chs = cur_root['children']
        for ch in chs:
            tmp_list.extend(SIM_IDS_(ch, node_list))
    # tmp_list.append(")")
    # tmp_list.append(str)
    return tmp_list

def get_simids_structure(ast):
    ast = json.loads(ast)
    ast_sbt = SIM_IDS_(0, ast)
    return ' '.join(map(str, ast_sbt))








def hump2underline(hunp_str):
    '''
    밑줄을 칠 CamelCase 문자열
    :param hunp_str: CamelCase 밑줄
    :return: 모두 소문자로 된 밑줄이 그어진 문자열
    '''
    p = re.compile(r'([a-z]|\d)([A-Z])') # 일반 일치, 소문자와 대문자의 경계 일치
    sub = re.sub(p, r'\1 \2', hunp_str).lower() # 여기서 두 번째 매개변수는 일반 그룹화된 역참조를 사용
    return sub






# code processing
def split_code(lines):
    result = []
    for line in lines:
        code = COMMENT_RX.sub('', line)
        processed_code = process_source(code)
        code_seq = ' '.join([hump2underline(i) for i in processed_code.split()])
        result.append(code_seq)
    
    return result

# def transformer3(code):
# #    code = COMMENT_RX.sub('', code)
# #    code = SPACE_RX.sub(' ', code)
#     processed_code = process_source(code)
#     code_seq = ' '.join([i for i in processed_code.split()])
#     ast = get_ast(processed_code)
#     sbt_num = get_sbt_num(ast)
#     sbt = get_sbt_structure(ast)
#     return code_seq, sbt, sbt_num

# return
def get_isbtcode(code):
    processed_code = process_source(code)
    ast = get_ast(processed_code)
    isbtcode = get_isbtcode_structure(ast)
    return isbtcode

def get_ids(code):
    processed_code = process_source(code)
    ast = get_ast(processed_code)
    ids = get_ids_structure(ast)
    return ids

def get_simsbtcode(code):
    code = COMMENT_RX.sub('', code)

    processed_code = process_source(code)
    ast = get_ast(processed_code)
    simsbtcode = get_simsbtcode(ast)
    return simsbtcode

def get_simids(code):
    code = COMMENT_RX.sub('', code)
    
    processed_code = process_source(code)
    ast = get_ast(processed_code)
    simids = get_simids_structure(ast)
    return simids