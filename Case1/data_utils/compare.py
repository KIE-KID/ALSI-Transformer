# sbt 길이와 ids 길이 비교
def compare(sbt, ids):
    sbt_list = []
    ids_list = []
    with open(sbt, 'r') as sbts:
        sbt = sbts.readlines()
        print(len(sbt))
        for s in sbt:
            tmp = s.split(' ')
            sbt_list.append(len(tmp))
    with open(ids, 'r') as isds:
        ids = isds.readlines()
        for i in ids:
            tmp2 = i.split(' ')
            ids_list.append(len(tmp2))

    print(sbt_list[0:10], ids_list[0:10])
    for i in range(len(sbt_list)):
        if sbt_list[i] != ids_list[i]:
            print(False)

compare('./train/sbt', './train/ids')
