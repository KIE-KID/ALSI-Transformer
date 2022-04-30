import dataset
import Model
import tensorflow as tf
import os
import nltk
import random
import time
import datetime
from nltk.translate.bleu_score import sentence_bleu, corpus_bleu
from nltk.translate.bleu_score import SmoothingFunction

os.environ['CUDA_VISIBLE_DEVICES'] = '1'
REGULARIZER = 0.0001
BATCH_SIZE = 32

output_dir = os.path.join(
        './result/train/', datetime.datetime.now().strftime('%Y-%m-%d'))  # _%H-%M-%S
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

MODEL_SAVE_PATH = "model"
MODEL_NAME = "nl"


def train():
    print('load data......')
    trainData = dataset.get_Data(BATCH_SIZE, "train")
    validData = dataset.get_Data(BATCH_SIZE, "valid")
    bacth_num = len(trainData[0])
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
        maxCBleu = 0
        nowCBleu = 0
        maxSBleu = 0
        nowSBleu = 0
        time_start = time.time()
        while True:
            index = list(range(len(trainData[0])))
            random.shuffle(index)
            for j in index:
                batch = len(trainData[0][j])
                gstep, rate, cost, _ = sess.run([model.add_global, model.learning_rate, model.cost, model.train_op],
                                                feed_dict={
                                                    model.ast_input: trainData[0][j],
                                                    # model.father: trainData[1][j],
                                                    model.ast_size: trainData[1][j],
                                                    model.ast_mask: trainData[2][j],
                                                    model.code_input: trainData[3][j],
                                                    model.code_size: trainData[4][j],
                                                    model.code_mask: trainData[5][j],
                                                    model.nl_input: trainData[6][j],
                                                    model.nl_output: trainData[7][j],
                                                    model.mask_size: trainData[8][j],
                                                    model.index: [list(range(1, 301))] * batch,
                                                    model.index1: [list(range(1, 31))] * batch,
                                                    model.index3: [list(range(1, 301))] * batch,
                                                    model.nlsize: [30]*batch,
                                                    model.training: True
                                                })

                if gstep % 100 == 0:
                    f = open(output_dir+'/out.txt', 'a')
                    s = 'After %d steps, rate is %.5f.  cost is %.5f, In iterator: %d. nowCBleu: %.5f, maxCBlue: %.5f. nowSBleu: %.5f, maxSBlue: %.5f.' % (
                        gstep, rate, cost, gstep // bacth_num, nowCBleu, maxCBleu, nowSBleu, maxSBleu)
                    f.write(s)
                    f.write('\n')
                    f.close()
                if gstep % 5000 == 0:
                    nowCBleu, nowSBleu = val(sess, model, validData)
                    if nowCBleu > maxCBleu:
                        maxCBleu = nowCBleu
                        saver.save(sess, os.path.join(MODEL_SAVE_PATH, MODEL_NAME), global_step=gstep)
                    if nowSBleu > maxSBleu:
                        maxSBleu = nowSBleu
            if gstep >= 500000:
                time_end = time.time()
                print('time cost', time_end - time_start, 's')

                f = open(output_dir+'/out2.txt', 'a')
                f.write(str(time_end - time_start))
                f.write('\n')
                f.close()
                return


def val(sess, model, data):
    smooth = SmoothingFunction()
    NL = data[4]
    cbleu = 0
    count = 0
    refs = []
    hpys = []
    for i in range(len(data[0])):
        batch = len(data[0][i])
        predic = sess.run(model.predict,
                          feed_dict={
                              model.ast_input: data[0][i],
                            #   model.father: data[1][i],
                              model.ast_size: data[1][i],
                              model.ast_mask: data[2][i],
                              model.code_input: data[3][i],
                              model.code_size: data[4][i],
                              model.code_mask: data[5][i],
                              model.nl_input: data[6][i],
                              model.index: [list(range(1, 301))] * batch,
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
                count += 1
            hpys.append(hpy)
            refs.append([NL[i][j]])
            if j == 0:
                print(hpy)
                print(NL[i][j])
                print('\n')

    if count > 1:
        cbleu = cbleu / count
    sbleu = corpus_bleu(refs, hpys, smoothing_function=smooth.method4)
    return cbleu, sbleu


f = open('newsbt_data/vocabulary/nl', 'r', encoding='utf-8')
s = f.readlines()
f.close()
dic_word = {}
key = 0
for c in s:
    dic_word[key] = c.strip()
    key += 1

train()
