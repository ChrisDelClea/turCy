import os
import sys
import re
import json
import importlib.resources

import spacy
from turcy.pattern import Pattern
from turcy.utils import save_jsonl
import string

def set_part(pattern, token, trip_d, trl_part_len=list):
    subj = trip_d[0]
    pred = trip_d[1]
    obj = trip_d[2]

    if token.text in [tok.text for tok in subj] and trl_part_len[0]>0:
        pattern.part = "subj"
        for idx, tok in enumerate([tok for tok in subj]):
            if token.text == tok.text:
                pattern.posi = subj[idx].i
                trl_part_len[0] -= 1
    elif token.text in [tok.text for tok in pred] and trl_part_len[1]>0:
        pattern.part = "pred"
        for idx, tok in enumerate([tok for tok in pred]):
            if token.text == tok.text:
                pattern.posi = pred[idx].i
                trl_part_len[1] -= 1
    elif token.text in [tok.text for tok in obj] and trl_part_len[2]>0:
        pattern.part = "obj"
        for idx, tok in enumerate([tok for tok in obj]):
            if token.text == tok.text:
                pattern.posi = obj[idx].i
                trl_part_len[2] -= 1

def loopTree(pattern, rootPattern):
    update_completness(pattern, rootPattern)
    for left in pattern.lefts:
        loopTree(left, rootPattern)
    for right in pattern.rights:
        loopTree(right, rootPattern)
    if rootPattern.subj and rootPattern.pred and rootPattern.obj:
        rootPattern.complete = True
        return 1
    else:
        return 0

def update_completness(pattern, rootPattern):
    if pattern.part == "subj":
        rootPattern.subj = True
        rootPattern.truth+=1
    elif pattern.part == "pred":
        rootPattern.pred = True
        rootPattern.truth += 1
    elif pattern.part == "obj":
        rootPattern.obj = True
        rootPattern.truth += 1

def build(token, patternTree=None, path="", triple=None, first=False, trip_d=None, count_key=None, trl_part_len=None):
    pattern = Pattern(tag_=token.tag_, dep_=token.dep_, keep=False, name=count_key)
    if first != True:
        patternTree[path].append(pattern)
    else:
        patternTree = pattern
    if token.text in triple:
        set_part(pattern, token, trip_d, trl_part_len)
        pattern.keep = True
        triple.remove(token.text)
    elif any(token.text in word for word in triple):
        part = [part for part in triple if token.text in part]
        part_idx = triple.index(part[0])
        words = part[0].split()
        for word in words:
            if word == token.text:
                pattern.keep = True
                set_part(pattern, token, trip_d, trl_part_len)
                triple[part_idx] = triple[part_idx].replace(token.text, '').strip()
                break
        for idx, trip in enumerate(triple):
            if trip.isspace() or all(i in string.punctuation for i in trip):
                del triple[idx]
        if len(triple)==0:
            return patternTree
    lefts = [token for token in token.lefts]
    rights = [token for token in token.rights]
    for left in lefts:
        patternTree = build(left, pattern, triple=triple, path="lefts", first=False, trip_d=trip_d, trl_part_len=trl_part_len)
    for right in rights:
        patternTree = build(right, pattern, triple=triple, path="rights", first=False, trip_d=trip_d, trl_part_len=trl_part_len)
    return patternTree


def doc_length(doc):
    length = len([token for token in doc])
    return length

nlp = spacy.load('de_core_news_lg')

def find(sent, triple, key=""):
    count = 0
    count_key = key + "_" + str(count)
    count+=1
    subj = triple[0]
    pred = triple[1]
    obj  = triple[2]
    trip = [subj, pred, obj]
    subj_doc = nlp(triple[0])
    pred_doc = nlp(triple[1])
    obj_doc  = nlp(triple[2])
    trip_d = [subj_doc, pred_doc, obj_doc]
    doc = nlp(sent)
    for token in doc:
        if token.dep_ == "ROOT":
            root_token = token
            break
    trl_part_len = [doc_length(subj_doc), doc_length(pred_doc), doc_length(obj_doc)] #trl_part_len
    pattern = build(root_token, triple=trip, first=True, trip_d=trip_d, count_key=count_key, trl_part_len=trl_part_len)
    # check if it's a complete pattern
    loopTree(pattern, pattern)
    return pattern

def add(pattern, pattern_list):
    if len(pattern) > 0:
        with importlib.resources.path("turcy", f"patterns_{pattern_list}.jsonl") as outfile:
            with open(str(outfile), 'a', encoding="utf8") as out_f:
                    json.dump(pattern, out_f)
                    out_f.write('\n') #.write('\n')