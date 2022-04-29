import argparse
from tokenizers import BertWordPieceTokenizer

parser = argparse.ArgumentParser()

parser.add_argument("--corpus_file", type=str)
parser.add_argument("--vocab_size", type=int, default=52000) # 만들 Vocab의 숫자 
parser.add_argument("--limit_alphabet", type=int, default=6000)

args = parser.parse_args()

tokenizer = BertWordPieceTokenizer(
    vocab=None,
    clean_text=True,
    handle_chinese_chars=True,
    strip_accents=False, # Must be False if cased model
    lowercase=False,
    wordpieces_prefix="##"
)

tokenizer.train(
    files=[args.corpus_file],
    limit_alphabet=args.limit_alphabet,
    vocab_size=args.vocab_size
)

tokenizer.save("./wp-vocab-{}-{}".format(args.limit_alphabet, args.vocab_size),True)