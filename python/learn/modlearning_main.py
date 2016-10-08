# coding: utf-8
import logging, gc, time, pickle, os
import sys, numpy as np
from tqdm import tqdm

from gensim.models import word2vec
import scipy.spatial.distance as distance
from scipy import sparse
from sklearn.ensemble import RandomForestClassifier
from sklearn.cross_validation import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.svm import LinearSVC
from sklearn.svm import SVC
from sklearn.linear_model import Perceptron
from sklearn.decomposition import PCA



def test_predict(filename_list, baseline, classfier, vocablist, target_list):
    print ("start predict process")
    for filename in filename_list:
        #target_list = {["filename_head","label"], ...,}
        for target in target_list:
            if filename.find(target[0]) != -1:
                label_list.append(target[1])
        sentence = word2vec.Text8Corpus(filename)
        output = classfier.predict([_test_train_model(baseline, sentence, classfier, vocablist)])
        print ("filename: %s , predict: %s" % (filename, output[0]))
    print("finished all train_model")
    #with open("classfier_age.pickle", "w") as fp:
    #    pickle.dump(classfier, fp)
    #index = len(arylist)-5
    #test_random_forest(arylist[:index], label_list[:index], arylist[index:])
    #input_random_forest(filename_vec, label)
def _test_train_model(baseline, sentence, classfier, vocablist):
    train_model = word2vec.Word2Vec.load(baseline)
    train_model.train(sentences=sentence)
    return vector_outputer(train_model, vocablist)




def test_random_forest(vector, label, classfier=None):
    print("RandomForestClassifier")
    if classfier is None:
        classfier = RandomForestClassifier(n_estimators=1000)
    classfier.fit(vector, label)
    print ("finished learing")
    return classfier
def vector_outputer(model, vocablist=None):
    norm = lambda x: np.linalg.norm(x)
    if vocablist is None:
        vocablist = model.vocab.keys()
    ary = []
    for k in vocablist:
        #ary += model[k.decode("utf-8")].tolist()
        ary.append(norm(model[k.decode("utf-8")]).tolist())
        #ary.append(model[k.decode("utf-8")].tolist())
    # n dimension vector
    #print ("finished vector")
    #pca = PCA(n_components=100)
    #ret = []
    #for v in pca.fit_transform(ary).tolist():
    #    ret += v
    #return ret
    return ary
    #return ary

def vector_outputer_cos(train_model, base_value, vocablist):
    vocab_len = len(vocablist)
    ary = sparse.lil_matrix((1, vocab_len))
    for (i, k) in enumerate(vocablist):
        if k.decode("utf-8") not in base_value:
            ary[0, i] = 0.0
            continue
        tmp = distance.cosine(base_value[k.decode("utf-8")].tolist(), train_model[k.decode("utf-8")].tolist())
        if tmp <= 0.05 and tmp >= -0.05:
            tmp = 0.0
        ary[0, i] = tmp
    return ary

def load_ary():
    ary = []
    with open("tmp_ary.pickle") as fp:
        while True:
            try:
                ary.append(pickle.load(fp))
            except:
                break
    return ary

def train_model(filename_list, baseline, vocablist, target_list):
    if os.path.exists("tmp_ary.pickle"):
        os.remove("tmp_ary.pickle")
    with open("tmp_ary.pickle", "a") as fp:
        base_model = word2vec.Word2Vec.load(baseline)
        reset_model = word2vec.Word2Vec.load(baseline)
        base_value = {}
        for k in vocablist:
            base_value[k.decode("utf-8")] = base_model[k.decode("utf-8")]
        print ("start process")
        arylist = []
        label_list = []
        for filename in tqdm(filename_list):
            #target_list = [["filename_head","label"], ...,]
            for target in target_list:
                if filename.find(target[0]) != -1:
                    label_list.append(target[1])
            sentence = word2vec.Text8Corpus(filename)
            base_model.train(sentences=sentence)
            arylist.append(vector_outputer_cos(base_model, base_value, vocablist))
            if len(arylist) > 10:
                pickle.dump(fp)
                arylist = []
            #reset base_model value
            base_model.reset_from(reset_model)
    print("finished all train_model")
    data = {"array_list" : load_ary(), "label_list" : label_list}
    with open("cos_vector_dic.pickle", "w") as fp:
        pickle.dump(data, fp)



def model_diff_vocabs(baseline, filename_list, rank=500):
    norm = lambda x: np.linalg.norm(x)
    train_model = word2vec.Word2Vec.load(baseline)
    base_model  = word2vec.Word2Vec.load(baseline)

    for filename in tqdm(filename_list):
        sentence = word2vec.Text8Corpus(filename)
        train_model.train(sentences=sentence)
    model_diff = {}
    print ("finished train_model")
    for k in tqdm(base_model.vocab.keys()):
        tmp_diff = norm(train_model[k]) - norm(base_model[k])
        if tmp_diff == 0.0:
            continue
        model_diff[k] = tmp_diff
    vocab_rank = []
    #count = 0
    with open("attr_vocab_all.txt", "w") as fp:
        for k, v in sorted(model_diff.items(), key=lambda x: x[1]):
            #count += 1
            fp.write(k.encode("utf-8"))
            fp.write("\n")
    #        if count > rank:
    #            break
    print ("finished model_diff")


def test_report_predict(vector, label, classfier=None):
    #print ("Perceptron")
    #print ("SVM")
    X_train, X_test, y_train, y_test = train_test_split(vector, label, test_size=0.4, random_state=0)
    #classfier = RandomForestRegressor(n_estimators=1000, criterion="entropy")
    #classfier = LinearSVC(C=1.0)
    #tmp = _eqlaus_number(X_train, y_train)
    print ("RandomForest n=1000")
    classfier = RandomForestClassifier(n_estimators=1000)
    classfier.fit(X_train, y_train)
    y_true, y_pred = y_test, classfier.predict(X_test)
    print (classification_report(y_true, y_pred))
    #print (len(tmp[0]), len(tmp[1]))
    #classfier.fit(tmp[0], tmp[1])
    print ("SVM rbf C=7.0 gamma=1.0")
    classfier = SVC(C=7.0, kernel="rbf", gamma=1.0)
    classfier.fit(X_train, y_train)
    y_true, y_pred = y_test, classfier.predict(X_test)
    print (classification_report(y_true, y_pred))
    #y_true, y_pred = y_train, classfier.predict(X_train)
    #with open("classfier_age.pickle", "w") as fp:
    #    pickle.dump(classfier, fp)




if __name__ == "__main__":
    filename_list = sys.argv[1].split("\n")[:-1]
    #print (filename_list[1].split("\n")[:9])
    target_list = [
                    ["house", "主婦"],
                    ["society", "社会人"],
                    ["students", "学生"]]

    baseline = "/home/word2cec_test_attribute/baseline_jawiki.txt.model"
    #model_diff_vocabs(baseline, filename_list)
    with open("attr_vocab_all.txt", "r") as fp:
        vocablist = fp.read().split("\n")[:-1]
    train_model(filename_list, baseline, vocablist, target_list)
    #with open("classfier_age.pickle", "r") as fp:
    #   classfier = pickle.load(fp)
    #train_model_report(filename_list, baseline, vocablist)
    #test_predict(filename_list, baseline, classfier, vocablist)
    #with open("vector_dic.pickle") as fp:
    #    vector_dic = pickle.load(fp)
    #test_forest_report_vector(vector_dic["array_list"], vector_dic["label_list"])
    #test_report_predict(vector_dic["array_list"], vector_dic["label_list"], classfier)


