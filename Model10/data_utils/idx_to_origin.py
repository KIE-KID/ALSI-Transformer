def code_to_origin(code, vocab):
    with open(code, 'r') as codes:
        line = codes.readlines()
        for c in line:
            str_token = []
            code_token = c.split(' ')
            code_token.pop()
            with open(vocab, 'r') as vocabs:
                vocabline = vocabs.readlines()
                for i in code_token:
                    code_str = vocabline[int(i)].replace('\n', '')
                    str_token.append(code_str)
                    with open('code_str', 'w') as out:
                        out.write((' ').join(str_token))


def sbt_to_origin(sbt, vocab):
    with open(sbt, 'r') as sbts:
        line = sbts.readlines()
        for s in line:
            str_token = []
            sbt_token = s.split(' ')
            sbt_token.pop()
            with open(vocab, 'r') as vocabs:
                vocabline = vocabs.readlines()
                for i in sbt_token:
                    sbt_str = vocabline[int(i)].replace('\n', '')
                    str_token.append(sbt_str)
                    with open('./data/data3/train/sbt_str', 'w') as out:
                        out.write((' ').join(str_token))
            

code_to_origin('./temp2/test/code', './temp2/vocabulary/code')
# sbt_to_origin('./data/data3/train/sbt_c', './data/data3/vocabulary/sbt')
            
                    