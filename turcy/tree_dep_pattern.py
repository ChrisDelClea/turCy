import os
import numpy as np
import pandas as pd
from numpy import dot
from numpy.linalg import norm
from typing import List
import json
from itertools import cycle

import spacy
from spacy import displacy
from spacy.tokens import Doc, Span, Token
from spacy.language import Language

from turcy.pattern import Pattern


def get_root(doc):
    for token in doc:
        if token.dep_  == "ROOT":
            return token


def is_subtree(mainTree, subTree, triple=None, ll=None) -> List:
    """ Main sub-tree search function of the package. Searches recursively for pattern matches.
    Args
        :param mainTree: The word/token tree build form the input sentence.
        :param subTree: The word/token tree from the pattern list.
        :param triple: The triple parts to pass on recursively and to eventually return.
        :param ll: helping list.
    Returns
        :return: Matched Triples .
    """
    triples = []

    if triple == None:
        triple = []
    if ll == None:
        ll = []

    if (subTree == None):
        if len(triple)>0:
            triples.append(triple)
            return triples
        else:
            return []

    if (mainTree == None):
        return []

    main_tree_lefts = [left_c for left_c in mainTree.lefts]
    main_tree_rights = [rigth_c for rigth_c in mainTree.rights if ( (rigth_c.text != ".")
                                                                    and (rigth_c.text != "(")
                                                                    and (rigth_c.text != ")")
                                                                    and (rigth_c.text != ",")
                                                                    and (rigth_c.text != ":"))]
    sub_tree_lefts = [left_c for left_c in subTree.lefts]
    sub_tree_rights = [rigth_c for rigth_c in subTree.rights if ((rigth_c.tag_ != "$.")
                                                                 and (rigth_c.tag_ != "$(")
                                                                 and (rigth_c.tag_ != "$,"))]

    if len(main_tree_lefts)<=0:
        main_tree_lefts.append(None)
    if len(main_tree_rights)<=0:
        main_tree_rights.append(None)
    if len(sub_tree_lefts)<=0:
        sub_tree_lefts.append(None)
    if len(sub_tree_rights)<=0:
        sub_tree_rights.append(None)

    main_tree = list(zip(main_tree_lefts, cycle(main_tree_rights))
                     if len(main_tree_lefts) > len(main_tree_rights)
                     else zip(cycle(main_tree_lefts), main_tree_rights))
    sub_tree = list(zip(sub_tree_lefts, cycle(sub_tree_rights))
                    if len(sub_tree_lefts) > len(sub_tree_rights)
                    else zip(cycle(sub_tree_lefts), sub_tree_rights))
    ll = list(zip(main_tree, sub_tree))
    for idx, (main, sub) in enumerate(ll):
        left_main_tree, right_main_tree = main
        left_sub_tree, right_sub_tree = sub
        # print(main_tree_left, main_tree_right)

        if ( (mainTree.tag_ == subTree.tag_) and mainTree.tag_ != "$," and mainTree.dep_ == subTree.dep_):
            if mainTree not in triple:
                if subTree.keep:
                    mainTree._.posi = subTree.posi
                    mainTree._.part = subTree.part
                    triple.append(mainTree)
            leftTree = is_subtree(left_main_tree, left_sub_tree, triple[:], ll[:])
            rightTree = is_subtree(right_main_tree, right_sub_tree, triple[:], ll[:])
            triples = is_appendable(leftTree, rightTree, left_sub_tree, right_sub_tree, triples)
            if len(ll)-1 == idx: # or subTree.truth == len(triples[0])
                return triples
        elif (len(triple)>0):
            return []
    triples.extend(is_subtree(left_main_tree, subTree))
    triples.extend(is_subtree(right_main_tree, subTree))
    return triples


def expand_tree_items(tree):
    new_tree = []
    for lis in tree:
        for token in lis:
            if token not in new_tree:
                new_tree.append(token)
    return new_tree


def is_subset(expanded_triple, triples)->bool:
    is_subset = False
    for triple in triples:
        sorted(triple)
        for trip in expanded_triple:
            sorted(trip)
            set1 = set(triple)
            set2 = set(trip)
            is_subset = set2.issubset(set1)
            # return is_subset
    return is_subset


def is_appendable(leftTree, rightTree, leftSubTree, rightSubTree, triples):
    if ((len(rightTree) > 0 and rightSubTree != None) and (len(leftTree) == 0)):
        if not is_subset(rightTree, triples):
            # right tree has already a part, merge new and old.
            if any(triples):
                right_tree = expand_tree_items(rightTree)
                old_tree = expand_tree_items(triples)
                expanded_triple = [old_tree + [l for l in right_tree if l not in old_tree]]
                return expanded_triple
            else:
                return rightTree
        else:
            return triples
    # 2.2 Found in right only
    elif ((len(leftTree) > 0 and leftSubTree != None) and (len(rightTree) == 0)):
        if not is_subset(leftTree, triples):
            # left tree has already a part, merge new and old.
            if any(triples):
                left_tree = expand_tree_items(rightTree)
                old_tree = expand_tree_items(triples)
                expanded_triple = [old_tree + [l for l in left_tree if l not in old_tree]]
                return expanded_triple
            return leftTree
        else:
            return triples
    # Found some triple, in both, resolve issue
    if len(leftTree) > 0 and len(rightTree) > 0:
        if leftTree == rightTree:
            triples.extend(leftTree)
        elif leftTree[0][0] == rightTree[0][0]:
            left_tree = expand_tree_items(leftTree) # added
            right_tree = expand_tree_items(rightTree)
            expanded_triple = [left_tree + [l for l in right_tree if l not in left_tree]]#added
            if not is_subset(expanded_triple, triples):
                left_tree = expand_tree_items(triples)
                right_tree = expand_tree_items(expanded_triple)
                triples.extend([left_tree + [l for l in right_tree if l not in left_tree]])
                if len(triples) == 2:
                    while len(triples) > 1:
                        del triples[0]
        else:
            left_tree = expand_tree_items(leftTree)
            right_tree = expand_tree_items(rightTree)
            triples.extend([left_tree + [l for l in right_tree if l not in left_tree]])
            if len(triples)==2:
                triples.extend([triples[1] + [l for l in triples[0] if l not in triples[1]]])
                while len(triples)>1:
                    del triples[0]
    return triples


def pattern_loader(path_to_rules="patterns.jsonl") -> List:
    """ Loads the patterns from the pattern list. """
    patterns = []
    patternDicts = []
    with open(path_to_rules, encoding="utf8") as f:
        try:
            for line in f:
                data = json.loads(line)
                patternDicts.append(data)
        except:
            pass
    for patternDict in patternDicts:
        patterns.append(Pattern(**patternDict))
    return patterns

def reassemble(tripleList):
    """ Reassembles the triples that were found to be in the right order. """
    subj = ""
    subjL = {}
    pred = ""
    predL = {}
    obj = ""
    objL = {}
    for token in tripleList:
        if token._.part == "subj":
            subjL.update({token._.posi: token.text})
        elif token._.part == "pred":
            predL.update({token._.posi: token.text})
        elif token._.part == "obj":
            objL.update({token._.posi: token.text})
        else:
            raise Exception('Triple does not belong to any part (subj,pred,obj).')

    subj = " ".join(str(subjL[elem]) for elem in sorted(subjL))
    pred = " ".join(str(predL[elem]) for elem in sorted(predL))
    obj = " ".join(str(objL[elem]) for elem in sorted(objL))
    if subj != "" and pred != "" and obj != "":
        return (subj, pred, obj)
    else:
        return None

@Language.component('attach_triple2sentence')
def attach_triple2sentence(doc):
    """ Goes through all patterns and sentences and tries to derive triples if there are some.  """
    work_dir = os.path.dirname(os.path.realpath(__file__))
    file_dir = os.path.join(work_dir, "patterns.jsonl")
    patternList = pattern_loader(path_to_rules=file_dir)

    for sent in doc.sents:
        for pattern in patternList:
            subTreeMatch = is_subtree(get_root(sent), pattern)
            for tripleList in subTreeMatch:
                if len(tripleList) >= 3 and len(tripleList) == pattern.truth:
                    triples = reassemble(tripleList)
                    if triples != None:
                        sent._.triples.append({"triple": triples, "rule": pattern.name})
    return doc


def add_patterns(nlp):
    nlp.add_pipe(attach_triple2sentence, last=True)
    return nlp