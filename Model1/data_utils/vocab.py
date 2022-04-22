import os
from utils_park import *
import nltk
nltk.download('punkt')
from nltk import Text
from nltk.tokenize import word_tokenize

PAD = '<pad>'
UNK = '<unk>'
SOS = '<start>'
EOS = '<end>'

PAD_ID = 0
UNK_ID = 1
SOS_ID = 2
EOS_ID = 3

# make vocabulary from data
def make_token_instance(lines):
    tokens = []
    for line in lines:
        tokens.extend(word_tokenize(str(line))) # 문장을 단어로 tokenize

    t = Text(tokens) # Token을 기반으로 정보를 담기 위한 인스턴스

    return t

# print(len(nl_t), len(set(nl_t))) # 191785개의 단어가 t 객체에 있음, 중복 제거시 58422
def make_vocab(lines, dic_type, VOCAB_SIZE):
    t = make_token_instance(lines)
    
    if dic_type == 'nl':
        vocab = t.vocab().most_common(VOCAB_SIZE - 4) # 상위 vocab_size개의 단어만 보존 
        word_to_index = {word[0] : index + 4 for index, word in enumerate(vocab)} # 각 단어에 대해 고유한 정수 부여하기(indexing)

        word_to_index[PAD] = PAD_ID
        word_to_index[UNK] = UNK_ID
        word_to_index[SOS] = SOS_ID
        word_to_index[EOS] = EOS_ID
    else:
        vocab = t.vocab().most_common(VOCAB_SIZE - 2) # 상위 vocab_size개의 단어만 보존 
        word_to_index = {word[0] : index + 2 for index, word in enumerate(vocab)} # 각 단어에 대해 고유한 정수 부여하기(indexing)

        word_to_index[PAD] = 0
        word_to_index[UNK] = 1

    # sorted_nl_dic = sorted(word_to_index.items(), key=lambda x:x[1]) 
    vocab_list = [x[0] for x in sorted(word_to_index.items(), key=lambda x:x[1])] # value 기준으로 정렬하고 키값(토큰)만 추출
    return vocab_list

def initialize_vocabulary(vocab_path):
    """
    Initialize vocabulary from file.

    We assume the vocabulary is stored one-item-per-line, so a file:
      dog
      cat
    will result in a vocabulary {'dog': 0, 'cat': 1}, and a reversed vocabulary {0:'dog', 1:'cat'}.

    :param vocabulary_path: path to the file containing the vocabulary.
    :return:
      the vocabulary (a dictionary mapping string to integers), and
      the reversed vocabulary (a list, which reverses the vocabulary mapping).
    """
    if os.path.exists(vocab_path):
        lines = read_file(vocab_path)
        reverse_vocab = {}
        key = 0
        for c in lines:
          reverse_vocab[key] = c.strip()
          key += 1    
        vocab = dict([(x, y) for (y, x) in enumerate(lines)])
        return vocab, reverse_vocab
    else:
        raise ValueError("vocabulary file %s not found", vocab_path)


def sentence_to_idx(file_name, word2idx_dic, data_type):
    lines = read_file(file_name)

    encode2idx = [] 
    tks = []

    if data_type == "code":
        tokens = split_code(lines)
        for line in tokens:
            tks.append(word_tokenize(str(line))) # 문장을 단어로 tokenize
    else:
        for line in lines:
            tks.append(word_tokenize(str(line))) # 문장을 단어로 tokenize

    for line in tks: #입력 데이터에서 1줄씩 문장을 읽음 
        temp = [] 
        for w in line: #각 줄에서 1개씩 글자를 읽음 
    #    try: 
    #        temp.append(word_to_index[w]) # 글자를 해당되는 정수로 변환 
    #    except KeyError: # 단어 집합에 없는 단어일 경우 unk로 대체된다. 
    #        temp.append(word_to_index['unk']) # unk의 인덱스로 변환 
            temp.append(word2idx_dic.get(w, UNK_ID))
        encode2idx.append(temp)

    return encode2idx

def idx_to_sentence(file_name, word2idx_dic, data_type):
    lines = read_file(file_name)

    idx2encode = [] 
    tks = []

    for line in lines:
        tks.append(line.split(' ')) # 문장을 단어로 tokenize

    for line in tks: #입력 데이터에서 1줄씩 문장을 읽음 
        temp = [] 
        for w in line: #각 줄에서 1개씩 글자를 읽음 
    #    try: 
    #        temp.append(word_to_index[w]) # 글자를 해당되는 정수로 변환 
    #    except KeyError: # 단어 집합에 없는 단어일 경우 unk로 대체된다. 
    #        temp.append(word_to_index['unk']) # unk의 인덱스로 변환 
            temp.append(word2idx_dic.get(int(w), UNK ))
        idx2encode.append(temp)

    return idx2encode


def save_vocab(out_path, out_name, vocab):
    if not os.path.isdir(out_path):
        os.makedirs(out_path)
        
    with open(out_path+out_name, 'w', encoding='utf-8') as f:
        for i in vocab:
            f.write(i+'\n')


def save_idx_file(out_path, out_name, index_list):
    if not os.path.isdir(out_path):
        os.makedirs(out_path)

    with open(out_path+out_name, 'w', encoding='utf-8') as f:
        for line in index_list:
            f.write(' '.join(map(str, line)) + '\n')


def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines = list(map(lambda s: s.strip(), lines))
    return lines


def save_file(out_path, out_name, ids):
    if not os.path.isdir(out_path):
        os.makedirs(out_path)
        
    with open(out_path+out_name, 'w', encoding='utf-8') as f:
        for i in ids:
            f.write(i+'\n')
            