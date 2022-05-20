# 데이터 별 토큰 길이 비교
from pyparsing import line


def compare(file1, file2):
    data = []
    data2 = []
    with open(file1, 'r') as f:
        line = f.readlines()
        for l in line:
            tmp = l.split(' ')
            data.append(len(tmp))
    with open(file2, 'r') as f2:
        line2 = f2.readlines()
        for l2 in line2:
            tmp2 = l2.split(' ')
            data2.append(len(tmp2))

    print(data[0:10], data2[0:10])
    for i in range(len(data)):
        if data[i] != data2[i]:
            print(False)

compare('valid.token.code', 'valid.result2')