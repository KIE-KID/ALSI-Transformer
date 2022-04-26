import dataset
import Model
import tensorflow as tf
import os
import nltk
import random
import time
import datetime
import json
from nltk.translate.bleu_score import sentence_bleu, corpus_bleu
from nltk.translate.bleu_score import SmoothingFunction
#import argparse

#parser = argparse.ArgumentParser(description='parser') # 인자값을 받을 수 있는 인스턴스 생성

#parser.add_argument('--cuda', required=False, default='0', elp='cuda device')
#parser.add_argument('--model', required=True, help='model path')

#args = parser.parse_args() # 입력받은 인자값을 args에 저장 (type: namespace)

os.environ['CUDA_VISIBLE_DEVICES'] = '0'
REGULARIZER = 0.0001
BATCH_SIZE = 32

output_dir = os.path.join(
        './result/test/', datetime.datetime.now().strftime('%Y-%m-%d'))  # _%H-%M-%S
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

MODEL_SAVE_PATH = "model"
MODEL_NAME = "nl"


def train():
    print('load data......')
    # trainData = dataset.get_Data(BATCH_SIZE, "train")
    validData = dataset.get_Data(BATCH_SIZE, "test")
    bacth_num = 1
    print('load finish')
    initializer = tf.random_uniform_initializer(-0.02, 0.02)
    with tf.variable_scope('my_model', reuse=None, initializer=initializer):
        model = Model.Transformer(bacth_num)

    saver = tf.train.Saver()
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.853)
    with tf.Session(config=tf.ConfigProto(gpu_options=gpu_options)) as sess:
        tf.global_variables_initializer().run()
        tf.local_variables_initializer().run()
        ckpt = tf.train.get_checkpoint_state(MODEL_SAVE_PATH)
        if ckpt and ckpt.model_checkpoint_path:
            saver.restore(sess, ckpt.model_checkpoint_path)
        val(sess, model, validData)


def val(sess, model, data):
    smooth = SmoothingFunction()
    NL = data[5]  # data[8]
    cbleu = 0
    count = 0
    refs = []
    hpys = []
    hpyjson = {}
    refsjson = {}
    cutjson = 0
    for i in range(len(data[0])):
        batch = len(data[0][i])
        predic = sess.run(model.predict,
                          feed_dict={
                              model.ast_input: data[0][i],
                              model.father: data[1][i],
                              model.ast_size: data[2][i],
                              model.ast_mask: data[3][i],
                              # model.code_input: data[4][i],
                              # model.code_size: data[5][i],
                              # model.code_mask: data[6][i],
                              model.nl_input: data[7][i],
                              # model.index: [list(range(1, 201))] * batch,
                              model.index1: [list(range(1, 31))] * batch,
                              model.index3: [list(range(1, 301))] * batch,
                              model.nlsize: [30] * batch,
                              model.training: False
                          })
        for j in range(len(predic)):
            hpy = []
            for k in predic[j]:
                if dic_word[k] == '<end>':
                    break
                hpy.append(dic_word[k])
            if len(hpy) > 2:
                cbleu += nltk.translate.bleu([NL[i][j]],
                                             hpy, smoothing_function=smooth.method4)
                count += 1
            if len(hpy) > -1:
                s = ''
                for cw1 in NL[i][j]:
                    s += cw1 + ' '
                refsjson[cutjson] = [s]
                s = ''
                for cw1 in hpy:
                    s += cw1 + ' '
                hpyjson[cutjson] = [s]
                cutjson += 1
            hpys.append(hpy)
            refs.append([NL[i][j]])
            if j == 0:
                print(hpy)
                print(NL[i][j])
                print('\n')

    if count > 1:
        cbleu = cbleu / count
    sbleu = corpus_bleu(refs, hpys, smoothing_function=smooth.method4)
    print(cbleu, sbleu)

    f = open(output_dir + '/out3.txt', 'a')
    f.write('cbleu: ', str(cbleu)+'\n')
    f.write('sbleu: ', str(sbleu)+'\n')
    f.close()

    with open(output_dir + "refs.json", "a", encoding='utf-8') as f:
        json.dump(refsjson, f)
    with open(output_dir + "hpy.json", "a", encoding='utf-8') as f:
        json.dump(hpyjson, f)


f = open('data_RQ1/40000_vocab_park/vocab.nl', 'r', encoding='utf-8')
s = f.readlines()
f.close()
dic_word = {}
key = 0
for c in s:
    dic_word[key] = c.strip()
    key += 1

train()
