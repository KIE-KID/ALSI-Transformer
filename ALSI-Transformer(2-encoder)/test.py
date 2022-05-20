import dataset
import Model
import tensorflow as tf
import os
import nltk
nltk.download('wordnet')
nltk.download('omw-1.4')
import random
import time
import datetime
import json
from nltk.translate.bleu_score import sentence_bleu, corpus_bleu
from nltk.translate.bleu_score import SmoothingFunction
from nltk.translate.meteor_score import meteor_score
from rouge import Rouge

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
    NL = data[7]
    cbleu = 0
    bleu_1gram = 0
    bleu_2gram = 0
    bleu_3gram = 0
    bleu_4gram = 0
    meteor = 0
    rouge_l_f1 = 0 
    rouge_l_precision = 0 
    rouge_l_recall = 0 
    
    all_bleu = []
    all_meteor = []
    all_rouge = []  
    
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
                              # model.father: data[1][i],
                              model.ast_size: data[1][i],
                              model.ast_mask: data[2][i],
                              model.code_input: data[3][i],
                              model.code_size: data[4][i],
                              model.code_mask: data[5][i],
                              model.nl_input: data[6][i],
                              model.index: [list(range(1, 201))] * batch,
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
                
                cbleu += nltk.translate.bleu([NL[i][j]], hpy, smoothing_function=smooth.method4)
                all_bleu.append(nltk.translate.bleu([NL[i][j]], hpy, smoothing_function=smooth.method4))

                bleu_1gram += sentence_bleu([NL[i][j]], hpy, weights=(1, 0, 0, 0), smoothing_function=smooth.method4)
                bleu_2gram += sentence_bleu([NL[i][j]], hpy, weights=(0, 1, 0, 0), smoothing_function=smooth.method4)
                bleu_3gram += sentence_bleu([NL[i][j]], hpy, weights=(0, 0, 1, 0), smoothing_function=smooth.method4)
                bleu_4gram += sentence_bleu([NL[i][j]], hpy, weights=(0, 0, 0, 1), smoothing_function=smooth.method4)

                meteor += meteor_score([NL[i][j]], hpy)
                all_meteor.append(meteor_score([NL[i][j]], hpy))

                rouge = Rouge()
                try:
                    temp_rouge = rouge.get_scores(' '.join(NL[i][j]), ' '.join(hpy), avg=True)['rouge-l']
                    rouge_l_f1 += temp_rouge['f']
                    rouge_l_precision += temp_rouge['p']
                    rouge_l_recall += temp_rouge['r']
                    all_rouge.append(temp_rouge['f'])
                except:
                    print('hpy: ',hpy)

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
        bleu_1gram = bleu_1gram / count
        bleu_2gram = bleu_2gram / count
        bleu_3gram = bleu_3gram / count
        bleu_4gram = bleu_4gram / count
        meteor = meteor / count
        rouge_l_f1 = rouge_l_f1 / count
        rouge_l_precision = rouge_l_precision / count
        rouge_l_recall = rouge_l_recall / count 

    sbleu = corpus_bleu(refs, hpys, smoothing_function=smooth.method4)
    print(f'cbleu: {cbleu} sbleu: {sbleu}')
    print(f'1-Gram BLEU: {bleu_1gram:.6f}')
    print(f'2-Gram BLEU: {bleu_2gram:.6f}')
    print(f'3-Gram BLEU: {bleu_3gram:.6f}')
    print(f'4-Gram BLEU: {bleu_4gram:.6f}')
    print(f'METEOR: {meteor:.6f}')
    print(f'ROUGE-L F1 score: {rouge_l_f1:.6f}')
    print(f'ROUGE-L Presicion: {rouge_l_precision:.6f}')
    print(f'ROUGE-L Recall: {rouge_l_recall:.6f}')

    
    f = open(output_dir + '/out3.txt', 'a')
    f.write('sentence bleu: '+ str(cbleu)+'\n')
    f.write('corpus bleu: '+ str(sbleu)+'\n')
    f.write('1-Gram BLEU: '+ str(bleu_1gram)+'\n')
    f.write('2-Gram BLEU: '+ str(bleu_2gram)+'\n')
    f.write('3-Gram BLEU: '+ str(bleu_3gram)+'\n')
    f.write('4-Gram BLEU: '+ str(bleu_4gram)+'\n')
    f.write('METEOR: '+ str(meteor)+'\n')
    f.write('ROUGE-L F1 score: '+ str(rouge_l_f1)+'\n')
    f.write('ROUGE-L Precision: '+ str(rouge_l_precision)+'\n')
    f.write('ROUGE-L Recall: '+ str(rouge_l_recall)+'\n')
    f.close()

    f = open(output_dir + '/all_bleu.txt', 'a')
    f.write(','.join(map(str,all_bleu)))
    f.close()

    f = open(output_dir + '/all_meteor.txt', 'a')
    f.write(','.join(map(str,all_meteor)))
    f.close()
    
    f = open(output_dir + '/all_rouge.txt', 'a')
    f.write(','.join(map(str,all_rouge)))
    f.close()

    with open(output_dir + "/refs.json", "a", encoding='utf-8') as f:
        json.dump(refsjson, f)
    with open(output_dir + "/hpy.json", "a", encoding='utf-8') as f:
        json.dump(hpyjson, f)


f = open('newsbt_data/vocabulary/nl', 'r', encoding='utf-8')
s = f.readlines()
f.close()
dic_word = {}
key = 0
for c in s:
    dic_word[key] = c.strip()
    key += 1

train()
