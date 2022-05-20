code_leng = 500
nl_leng = 30

def get_Data(bath, path):
    codes = []
    codesizes = []
    codemasks = []

    inputNL = []
    outputNL = []
    nlopuputLeng = []

    f = open('newsbt_data/' + path + '/newsbtcode_camel_bpe', 'r', encoding='utf-8')
    CODEs = f.readlines()
    f.close()
    for temp in CODEs:
        code = [int(w) for w in temp.strip().split()]
        code = [2] + code + [3] # add <start>, <end> special tokens
        if len(code) > code_leng:
            code = code[0:code_leng]
        if len(code) % 2 == 0:
            lc = len(code) // 2
        else:
            lc = len(code) // 2 + 1
        codesizes.append(lc)
        codemasks.append([1] * lc + [0] * (code_leng//2 - lc))
        while len(code) < code_leng:
            code.append(0)
        codes.append(code)

    if path == 'train':
        f = open('newsbt_data/' + path + '/nl', 'r', encoding='utf-8')
        NLs = f.readlines()
        f.close()
        for temp in NLs:
            nl = [int(w) for w in temp.strip().split()]
            nl = [2] + nl + [3]
            inp = nl[0:-1]
            outp = nl[1:len(nl)]
            if len(inp) > nl_leng:
                inp = inp[0:nl_leng]
                outp = outp[0:nl_leng]
            nlopuputLeng.append(len(inp))
            while len(inp) < nl_leng:
                inp.append(0)
                outp.append(0)
            inputNL.append(inp)
            outputNL.append(outp)
    else:
        f = open('newsbt_data/' + path + '/nl.char', 'r', encoding='utf-8')
        NLs = f.readlines()
        f.close()
        for temp in NLs:
            nl = [w for w in temp.strip().split()]
            if len(nl) > nl_leng:
                nl = nl[:nl_leng]
            outputNL.append(nl)
            nlopuputLeng.append(len(nl))
            nl = [2]
            for i in range(nl_leng - 1):
                nl.append(0)
            inputNL.append(nl)

    bathcode = []
    bathcodesize = []
    bathcodemask = []
    bathinputNL = []
    bathoutputNL = []
    bathnloutputLeng = []
    start = 0
    while start < len(codes):
        end = min(start + bath, len(codes))
        bathcode.append(codes[start:end])
        bathcodesize.append(codesizes[start:end])
        bathcodemask.append(codemasks[start:end])

        bathinputNL.append(inputNL[start:end])
        bathoutputNL.append(outputNL[start:end])

        bathnloutputLeng.append(nlopuputLeng[start:end])
        start += bath
        
    return bathcode, bathcodesize, bathcodemask, bathinputNL, bathoutputNL, bathnloutputLeng
