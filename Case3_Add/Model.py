from encodings import CodecRegistryError
import tensorflow as tf
from modules import get_token_embeddings, ff, positional_encoding, multihead_attention, label_smoothing, noam_scheme
import numpy as np
import bert

VOCAB_SIZE = 40000
CODE_VOCAB_SIZE = 52000 #30002
SBT_VOCAB_SIZE = 52000 #40000
NL_VOCAB_SIZE = 40000 #23428
HIDDEN_SIZE = 768
NUM_LAYERS = 1
SHARE_EMB_AND_SOFTMAX = True
KEEP_PROB = 0.8
MAX_GRAD_NORM = 5

num_blocks = 3
head_num = 8
d_ff = 2048


class Transformer:
    def create_initializer(self, initializer_range=0.02):
        """Creates a `truncated_normal_initializer` with the given range."""
        return tf.truncated_normal_initializer(stddev=initializer_range)

    def weight_variable(self, shape):
        initial = tf.truncated_normal(shape, stddev=0.1)
        weight = tf.Variable(initial)
        tf.add_to_collection("losses", tf.contrib.layers.l2_regularizer(0.00005)(weight))
        return weight

    def bias_variable(self, shape):
        initial = tf.constant(0.1, shape=shape)
        return tf.Variable(initial)

    def __init__(self, bacth_num):
        self.nlLeng = 30
        self.codeLneg = 300 #200
        self.sbtLneg = 300
        self.bacth_num = bacth_num

        self.nl_embedding = tf.get_variable('nl_emb', [NL_VOCAB_SIZE, HIDDEN_SIZE])
        self.code_embedding = tf.get_variable('code_emb', [CODE_VOCAB_SIZE, HIDDEN_SIZE])
        self.ast_embedding = tf.get_variable('sbt_emb', [SBT_VOCAB_SIZE, HIDDEN_SIZE])

        E = HIDDEN_SIZE
        position_enc = np.array([
            [pos / np.power(10000, (i - i % 2) / E) for i in range(E)]
            for pos in range(600)]) #500
        position_enc[:, 0::2] = np.sin(position_enc[:, 0::2]) / 1000.0  # dim 2i
        position_enc[:, 1::2] = np.cos(position_enc[:, 1::2]) / 1000.0  # dim 2i+1)

        self.position_enc1 = tf.get_variable('pos_emb', shape=[600, HIDDEN_SIZE],
                                             initializer=self.create_initializer(0.002))



        self.ast_input = tf.placeholder(tf.int32, [None, self.sbtLneg])
        self.ast_size = tf.placeholder(tf.int32, [None])
        self.ast_mask = tf.placeholder(tf.int32, [None, self.sbtLneg // 2])
    
        self.code_input = tf.placeholder(tf.int32, [None, self.codeLneg])
        self.code_size = tf.placeholder(tf.int32, [None])
        self.code_mask = tf.placeholder(tf.int32, [None, self.codeLneg // 2])


        self.index = tf.placeholder(tf.int32, [None, self.codeLneg])
        self.index1 = tf.placeholder(tf.int32, [None, self.nlLeng])
        self.index3 = tf.placeholder(tf.int32, [None, self.sbtLneg])
        self.nlsize = tf.placeholder(tf.int32, [None])

        self.nl_input = tf.placeholder(tf.int32, [None, self.nlLeng])
        self.nl_output = tf.placeholder(tf.int32, [None, self.nlLeng])
        self.mask_size = tf.placeholder(tf.int32, [None])
        self.training = tf.placeholder(tf.bool)

        memory, tag_masks = self.encode_code(self.code_input, self.index, self.code_mask,
                                             self.ast_input, self.index3, self.ast_mask,
                                             training=self.training)


        self.cost, self.train_op, self.predict, self.learning_rate, self.add_global = self.mydecoder1(memory, tag_masks)

    def mydecoder1(self, memory, tag_masks):
        with tf.variable_scope('decoder1'):
            logits, preds = self.decode(self.nl_input, self.index1, memory, tag_masks, training=self.training)

            cost = tf.contrib.seq2seq.sequence_loss(logits=logits, targets=self.nl_output,
                                                    weights=tf.sequence_mask(self.mask_size,
                                                                             maxlen=tf.shape(self.nl_output)[1],
                                                                             dtype=tf.float32))

            global_step = tf.Variable(0, trainable=False)

            learning_rate = tf.train.exponential_decay(1e-4,
                                                       global_step=global_step,
                                                       decay_steps=self.bacth_num,
                                                       decay_rate=0.99,
                                                       staircase=True)

            train_op = tf.train.AdamOptimizer(learning_rate).minimize(cost)
            add_global = global_step.assign_add(1)

            decoder = self.nl_input
            for i in range(30):
                logits, preds = self.decode(decoder, self.index1, memory, tag_masks, training=self.training)
                if i < 29:
                    temp = tf.concat(axis=1, values=[decoder[:, :i + 1], preds[:, i:i + 1], decoder[:, i + 2:]])
                    decoder = temp

            predict = preds
            return cost, train_op, predict, learning_rate, add_global


    def encode_code(self, code_input, index, mask, ast_input, index3, mask3, training=True):
        '''
        Returns
        memory: encoder outputs. (N, T1, d_model)
        '''

        with tf.variable_scope("encoder_code", reuse=tf.AUTO_REUSE):
            enc_code = tf.nn.embedding_lookup(self.code_embedding, code_input)
            tgt_masks = tf.math.equal(mask, 0)  # (N, T1)
            posin = tf.nn.embedding_lookup(self.position_enc1, index)
            enc_code += posin
            enc_code = tf.layers.dropout(enc_code, 0.2, training=training)

            with tf.variable_scope("conv1", reuse=tf.AUTO_REUSE):
                enc_code = tf.reshape(enc_code, [-1, self.codeLneg, HIDDEN_SIZE, 1])
                conv1_w = self.weight_variable([3, 1, 1, 1])
                input_emb1 = tf.nn.conv2d(enc_code, conv1_w, strides=[1, 1, 1, 1], padding='SAME')
                input_emb1 = tf.nn.max_pool(input_emb1, ksize=[1, 2, 1, 1], strides=[1, 2, 1, 1], padding='VALID')
                enc_code = tf.reshape(input_emb1, [-1, self.codeLneg // 2, HIDDEN_SIZE])
                

            enc_ast = tf.nn.embedding_lookup(self.ast_embedding, ast_input)
            src_masks = tf.math.equal(mask3, 0)  # (N, T1)

            enc_ast = tf.layers.dropout(enc_ast, 0.2, training=training)

            enc_ast = tf.reshape(enc_ast, [-1, self.sbtLneg, HIDDEN_SIZE, 1])
            conv1_w = self.weight_variable([3, 1, 1, 1])
            input_emb1 = tf.nn.conv2d(enc_ast, conv1_w, strides=[1, 1, 1, 1], padding='SAME')
            input_emb1 = tf.nn.max_pool(input_emb1, ksize=[1, 2, 1, 1], strides=[1, 2, 1, 1], padding='VALID')
            enc_ast = tf.reshape(input_emb1, [-1, self.sbtLneg // 2, HIDDEN_SIZE])

            enc_both = tf.add(enc_code, enc_ast)


            mask_both = tf.logical_or(tgt_masks, src_masks)

            for i in range(num_blocks):
                with tf.variable_scope("num_blocks2_{}".format(i), reuse=tf.AUTO_REUSE):
                    enc_both = multihead_attention(queries=enc_both,
                                                   keys=enc_both,
                                                   values=enc_both,
                                                   key_masks=mask_both,
                                                   num_heads=head_num,
                                                   dropout_rate=0.2,
                                                   training=training,
                                                   causality=False,
                                                   scope="self_attention_code")
                    

                    temp_both = enc_both

                    enc_both = multihead_attention(queries=enc_both,
                                                   keys=temp_both,
                                                   values=temp_both,
                                                   key_masks=mask_both,
                                                   num_heads=head_num,
                                                   dropout_rate=0.2,
                                                   training=training,
                                                   causality=False,
                                                   scope="vanilla_attention_code")


                    enc_both = ff(enc_both, num_units=[d_ff, HIDDEN_SIZE])

            return enc_both, mask_both

    def decode(self, nl_input, index, memory, tag_masks, training=True):
    # (self, nl_input, index, memory, tag_masks, enc_ast, src_masks, training=True):

        with tf.variable_scope("decoder", reuse=tf.AUTO_REUSE):
            # tgt_masks
            tg_masks = tf.math.equal(nl_input, 0)  # (N, T2)

            # embedding
            dec = tf.nn.embedding_lookup(self.nl_embedding, nl_input)  # (N, T2, d_model)

            dec += tf.nn.embedding_lookup(self.position_enc1, index)
            dec = tf.layers.dropout(dec, 0.2, training=training)

            # Blocks
            for i in range(num_blocks):
                with tf.variable_scope("num_blocks3_{}".format(i), reuse=tf.AUTO_REUSE):
                    # Masked self-attention (Note that causality is True at this time)
                    dec = multihead_attention(queries=dec,
                                              keys=dec,
                                              values=dec,
                                              key_masks=tg_masks,
                                              num_heads=head_num,
                                              dropout_rate=0.2,
                                              training=training,
                                              causality=True,
                                              scope="self_attention")

                    # Vanilla attention
                    dec = multihead_attention(queries=dec,
                                              keys=memory,
                                              values=memory,
                                              key_masks=tag_masks,
                                              num_heads=head_num,
                                              dropout_rate=0.2,
                                              training=training,
                                              causality=False,
                                              scope="vanilla_attention_code")
                                              
                    dec = ff(dec, num_units=[d_ff, HIDDEN_SIZE])

        weights = tf.transpose(self.nl_embedding)  # (d_model, vocab_size)
        logits = tf.einsum('ntd,dk->ntk', dec, weights)  # (N, T2, vocab_size)
        y_hat = tf.to_int32(tf.argmax(logits, axis=-1))

        return logits, y_hat,

def gelu(x):
    """Gaussian Error Linear Unit.

    This is a smoother version of the RELU.
    Original paper: https://arxiv.org/abs/1606.08415
    Args:
      x: float Tensor to perform activation.

    Returns:
      `x` with the GELU activation applied.
    """
    cdf = 0.5 * (1.0 + tf.tanh(
        (np.sqrt(2 / np.pi) * (x + 0.044715 * tf.pow(x, 3)))))
    return x * cdf
