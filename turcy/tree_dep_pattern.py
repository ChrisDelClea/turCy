import numpy as np
import pandas as pd
import spacy
from spacy import displacy
from spacy.tokens import Doc, Span, Token
from numpy import dot
from numpy.linalg import norm
from typing import List
import json
from turcy.pattern import Pattern

def get_root(doc):
    for token in doc:
        if token.dep_  == "ROOT":
            return token

def merge_names(doc):
    with doc.retokenize() as retokenizer:
        for token in doc:
            lefts = [left_c for left_c in token.lefts]
            if len(lefts)>0:
                if lefts[0].tag_ == "NE" and lefts[0].dep_ == "pnc":
                    new_tok = doc[lefts[0].i : token.i+1]
                    retokenizer.merge(new_tok)

    with doc.retokenize() as retokenizer:
        for token in doc:
            rights = [right_c for right_c in token.rights]
            if len(rights)>0:
                if token.tag_ == "NE" and rights[0].tag_ == "NE" and rights[0].dep_ == "nk":
                    right_tok = doc[token.i : rights[0].i+1]
                    retokenizer.merge(right_tok)
    return doc

def merge_noun_chunks(doc):
    with doc.retokenize() as retokenizer:
        for cunk in doc.noun_chunks:
            retokenizer.merge(cunk)
    return doc

def merge_entities(doc):
    pass

def isSubtree(mainTree, subTree, triple=None) -> List:

    triples = []

    if triple == None:
        triple = []

    if (subTree == None):
        triples.append(triple)
        return triples

    if (mainTree == None):
        return []

    mainTreeLefts = [left_c for left_c in mainTree.lefts]
    mainTreeRights = [left_c for left_c in mainTree.rights]
    subTreeLefts = [left_c for left_c in subTree.lefts]
    subTreeRights = [left_c for left_c in subTree.rights]

    if len(mainTreeLefts) > 0:
        leftMainTree = mainTreeLefts[0]
    else:
        leftMainTree = None

    if len(mainTreeRights) > 0:
        if mainTreeRights[0].tag_ == "$,":
            rightMainTree = mainTreeRights[1]
        else:
            rightMainTree = mainTreeRights[0]
    else:
        rightMainTree = None

    if len(subTreeLefts) > 0:
        leftSubTree = subTreeLefts[0]
    else:
        leftSubTree = None

    if len(subTreeRights) > 0:
        rightSubTree = subTreeRights[0]
    else:
        rightSubTree = None

    if subTree.dep_ == None:
        if ((mainTree.tag_ == subTree.tag_) and mainTree.tag_ != "$,"):
            if subTree.keep:
                triple.append(mainTree)
            leftTreee = isSubtree(leftMainTree, leftSubTree, triple[:])
            rightTreee = isSubtree(rightMainTree, rightSubTree, triple[:])
            triples = isAppendable(leftTreee, rightTreee, leftSubTree, rightSubTree, triples)
            return triples

    elif ( (mainTree.tag_ == subTree.tag_) and mainTree.tag_ != "$," and mainTree.dep_ == subTree.dep_):
        if subTree.keep:
            triple.append(mainTree)
        leftTree = isSubtree(leftMainTree, leftSubTree, triple[:])
        rightTree = isSubtree(rightMainTree, rightSubTree, triple[:])
        triples = isAppendable(leftTree, rightTree, leftSubTree, rightSubTree, triples)
        return triples
    elif (len(triple)>0):
        return []
    triples.extend(isSubtree(leftMainTree, subTree))
    triples.extend(isSubtree(rightMainTree, subTree))
    return triples


def isAppendable(leftTree, rightTree, leftSubTree, rightSubTree, triples ):
    if (len(leftTree) == 0 and leftSubTree != None):
        return []
    elif (len(rightTree) == 0 and rightSubTree != None):
        return []
    if len(leftTree) > 0 and len(rightTree) > 0:
        if leftTree == rightTree:
            triples.extend(leftTree)
        elif leftTree[0][0] == rightTree[0][0]:
            triples.extend([rightTree[0] + [l for l in leftTree[0] if l not in rightTree[0]]])
        else:
            triples.extend([rightTree[0] + [l for l in leftTree[0] if l not in rightTree[0]]])
           # triples.extend(rightTree[0])
    return triples


#encoding="utf8"
def pattern_loader(path_to_rules="shared/data/rules.json") -> List:
    patterns = []
    with open(path_to_rules) as f:
        patternDicts = json.loads(f.read())
    for patternDict in patternDicts:
        patterns.append(Pattern(**patternDict))
    return patterns


def attach_triple2sentence(doc):
    patternList = pattern_loader()
    doc = merge_names(doc)
    for sent in doc.sents:
        for pattern in patternList:
            # if pattern.name == "n3":
                #print("stop")
            subTreeMatch = isSubtree(get_root(sent), pattern)
            for tripleList in subTreeMatch:
                if len(tripleList)==2:
                    if "i" in pattern.name:
                        if pattern.appendOrder == "inOrder":
                             sent._.triples.append({"triple": (tripleList[1].lemma_, "ist", tripleList[0].lemma_), "rule": pattern.name} )
                        elif pattern.appendOrder == "preOrder":
                            sent._.triples.append({"triple": (tripleList[0].lemma_, "ist", tripleList[1].lemma_), "rule": pattern.name})
                    elif "h" in pattern.name:
                        if pattern.appendOrder == "inOrder":
                             sent._.triples.append({"triple": (tripleList[1].lemma_, "hat", tripleList[0].lemma_), "rule": pattern.name} )
                        elif pattern.appendOrder == "preOrder":
                            sent._.triples.append({"triple": (tripleList[0].lemma_, "hat", tripleList[1].lemma_), "rule": pattern.name})
                elif len(tripleList) == 3:
                    if "p" in pattern.name:
                        sent._.triples.append(
                            {"triple": (tripleList[0].text, tripleList[1].text, tripleList[2].text), "rule": pattern.name})
                    elif "n" in pattern.name:
                        sent._.triples.append({"triple": (tripleList[2].lemma_, tripleList[0].lemma_, tripleList[1].lemma_), "rule": pattern.name})
                    else:
                        sent._.triples.append({"triple": (tripleList[2].lemma_, tripleList[0].text, tripleList[1].lemma_), "rule": pattern.name})
    return doc


def add_patterns(nlp):
    # nlp.add_pipe(merge_noun_chunks)
    nlp.add_pipe(attach_triple2sentence, last=True)
    return nlp


# def extract(user_input):
#     Doc.set_extension('triples', default=[], force=True)
#     Span.set_extension('triples', default=[], force=True)
#
#     nlp = spacy.load("de_core_news_lg")
#     lemma_lookup = nlp.vocab.lookups.get_table("lemma_lookup")
#     lemma_lookup["Amtskollegen"] = "Amtskollege"
#     lemma_lookup["Kanzlerin"] = "Kanzler"

    # "Student Christian Klose kommt aus Deutschland. "  # i1
    # "Der Präsident, Frank-Walter Steinmeier ließ verlauten, dass ... . "  # i2
    # "Barack Obama, einer der Präsidenten, ließ verlauten, dass der Traum von Freiheit tot ist. "  # i3
    # "Angela Merkel ist die Kanzlerin Deutschlands. "  # i4
    # "Der Kanzler Frankreichs heißt Emmanuel Macron. "  # h1
    # "Tobias trifft seinen Bruder Christian Klose. "  # h2
    # "Franz Schneider, dessen Frau Hausfrau ist, muss den Abwasch machen. "  # h3
    # "Die Kanzlerin von Deutschland, ist Frau Merkel."  # h4
    # "In Bayern in Deutschland können Sie vor allem im Frankenland die Natur genießen. "  # p1
    # # "Optimismus ist nur ein Mangel an Erfahrung." p2
    # "Auf Amerikas Präsident Joe Biden wartet schon ein Berg Arbeit. "  # n1
    # "All das gehörte nicht Deutschland, dessen Präsident Christian Wulff war. "  # n2
    # "Angela Merkel schüttelte ihrem Amtskollegen Vladimir Putin die Hand. "  # n3
    #

    # nlp = add_patterns(nlp)
    # doc = nlp(user_input)
    # # doc = attach_triple2sentence(doc, patternList)
    # df = pd.DataFrame(columns=["subj","pred", "obj", "rule"])
    # store = TripleStore()
    # for sent in doc.sents:
    #     for triple in sent._.triples:
    #         (subj, pred, obj) = triple["triple"]
    #         rule = triple["rule"]
    #         df = df.append({'subj': subj, 'pred':pred,'obj':obj,'rule':rule}, ignore_index=True)
    #         #st.write(subj, type(subj))
    #         #st.write(pred, type(pred))
    #         #st.write(obj, type(obj))
    #         # st.write(f"{subj}, {pred}, {obj}, {rule}")
    #         store.add_triple(subj, pred, obj, "")
    #         #st.write(triple)
    #         #tripleList.append(triple)
    # return df, store
