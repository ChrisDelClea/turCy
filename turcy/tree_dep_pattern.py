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

# def merge_names(doc):
#     with doc.retokenize() as retokenizer:
#         for token in doc:
#             lefts = [left_c for left_c in token.lefts]
#             if len(lefts)>0:
#                 if lefts[0].tag_ == "NE" and lefts[0].dep_ == "pnc":
#                     new_tok = doc[lefts[0].i : token.i+1]
#                     retokenizer.merge(new_tok)
#
#     with doc.retokenize() as retokenizer:
#         for token in doc:
#             rights = [right_c for right_c in token.rights]
#             if len(rights)>0:
#                 if token.tag_ == "NE" and rights[0].tag_ == "NE" and rights[0].dep_ == "nk":
#                     right_tok = doc[token.i : rights[0].i+1]
#                     retokenizer.merge(right_tok)
#     return doc

def isSubtree(mainTree, subTree, triple=None, ll=None) -> List:

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
            leftTree = isSubtree(left_main_tree, left_sub_tree, triple[:], ll[:])
            rightTree = isSubtree(right_main_tree, right_sub_tree, triple[:], ll[:])
            triples = isAppendable(leftTree, rightTree, left_sub_tree, right_sub_tree, triples)
            if len(ll)-1 == idx: # or subTree.truth == len(triples[0])
                return triples
        elif (len(triple)>0):
            return []
    triples.extend(isSubtree(left_main_tree, subTree))
    triples.extend(isSubtree(right_main_tree, subTree))
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

def isAppendable(leftTree, rightTree, leftSubTree, rightSubTree, triples ):
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
            # triples.extend([leftTree[0] + [l for l in rightTree[0] if l not in leftTree[0]]])
        else:
            left_tree = expand_tree_items(leftTree)
            right_tree = expand_tree_items(rightTree)
            triples.extend([left_tree + [l for l in right_tree if l not in left_tree]])
            if len(triples)==2:
                # right_triple = expand_tree_items(rightTree[1])
                triples.extend([triples[1] + [l for l in triples[0] if l not in triples[1]]])
                while len(triples)>1:
                    del triples[0]
    return triples


#encoding="utf8"
def pattern_loader(path_to_rules="patterns.jsonl") -> List:
    patterns = []
    patternDicts = []
    with open(path_to_rules, encoding="utf8") as f:
        try:
            for line in f:
                data = json.loads(line)
                patternDicts.append(data) # json.loads(f.read())
        except:
            pass
    for patternDict in patternDicts:
        patterns.append(Pattern(**patternDict))
    return patterns

def reassemble(tripleList):
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
    work_dir = os.path.dirname(os.path.realpath(__file__))
    file_dir = os.path.join(work_dir, "patterns.jsonl")
    patternList = pattern_loader(path_to_rules=file_dir)

    for sent in doc.sents:
        for pattern in patternList:
            subTreeMatch = isSubtree(get_root(sent), pattern)
            for tripleList in subTreeMatch:
                if len(tripleList) >= 3 and len(tripleList) == pattern.truth:
                    triples = reassemble(tripleList)
                    if triples != None:
                        sent._.triples.append({"triple": triples, "rule": pattern.name})
    return doc


def add_patterns(nlp):
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


# Drei Bruchpiloten in Paris (Originaltitel: La Grande vadrouille), in Deutschland auch unter dem Titel Die große Sause bekannt, ist eine französische Filmkomödie, bei der Gérard Oury Regie führte und die 1966 in die Kinos kam. The Drop – Bargeld ist ein US-amerikanisches Kriminalfilm-Drama des belgischen Regisseurs Michaël R. Roskam aus dem Jahr 2014. Das Drehbuch stammt von Autor Dennis Lehane, der dazu seine eigene Kurzgeschichte Animal Rescue verarbeitete. Im Jahr 1987 zählte Köttweinsdorf 117 Einwohner. Die EN 60601-2-27 mit dem Titel „Medizinische elektrische Geräte – Teil 2-27: Besondere Festlegungen für die Sicherheit von Elektrokardiographie-Überwachungsgeräten“ ist Teil der Normenreihe EN 60601. Herausgeber der DIN-Norm DIN EN 60601-2-27 ist das Deutsche Institut für Normung. Der HC Lev Poprad war ein 2010 gegründeter Eishockeyklub mit Sitz in der slowakischen Stadt Poprad. Quers ist eine Gemeinde im französischen Département Haute-Saône in der Region Bourgogne-Franche-Comté. Bacoor (offiziell: Municipality of Bacoor; Filipino: Bayan ng Bakoor) ist eine philippinische Stadtgemeinde in der Provinz Cavite. Der Lagonda 2.6 Litre war ein Oberklassefahrzeug, das der britische Automobilhersteller Aston Martin von 1948 bis 1953 unter dem Markennamen Lagonda anbot. Poręba Żegoty (örtlich Porymba Zegoty) ist ein Dorf mit einem Schulzenamt der Gemeinde Alwernia im Powiat Chrzanowski der Woiwodschaft Kleinpolen in Polen. Becklingen liegt etwa 7 km nördlich von Bergen an der Bundesstraße 3 und hat 362 Einwohner (Stand: 31. Juli 2015). Die Gmina Abramów ist eine Landgemeinde im Powiat Lubartowski der Woiwodschaft Lublin in Polen. Der Pegaso Z-102 ist ein Sportwagen, der von 1951 bis 1958 in Spanien gebaut wurde. Parbayse ist eine französische Gemeinde mit Einwohnern (Stand ) im Département Pyrénées-Atlantiques in der Region Nouvelle-Aquitaine (vor 2016: Aquitanien). Der Wahlbezirk Böhmen 102 war ein Wahlkreis für die Wahlen zum Abgeordnetenhaus im österreichischen Kronland Böhmen. Laihia (finnisch; schwedisch Laihela) ist eine Gemeinde in der westfinnischen Landschaft Österbotten. Tropico 4 ist eine von Haemimont Games entwickelte und vom Publisher Kalypso Media vertriebene Wirtschaftssimulation aus dem Jahr 2011. Das Spiel ist der vierte Teil der Wirtschaftsimulations-Reihe Tropico und der direkte Nachfolger von Tropico  3. Der Spieler übernimmt wie in den vorangegangenen Teilen die Rolle von „El Presidente“, dem Diktator der fiktiven Bananenrepublik Tropico. Das Hempstead County ist ein     County im Bundesstaat Arkansas. Der Unsichtbare kehrt zurück (Originaltitel: The Invisible Man Returns) ist ein US-amerikanischer Horror-/Science-Fiction-Film des Regisseurs Joe May aus dem Jahr 1940. Die Universal-Produktion wurde als Fortsetzung zu Der Unsichtbare (1933) gedreht und basiert lose auf einem Roman von H. G. Wells. Schigansk (; , Edjigeen) ist ein Dorf (selo) in der Republik Sacha (Jakutien) in Russland mit Einwohnern (Stand ). Neuküstrinchen ist ein Ortsteil der Gemeinde Oderaue im Landkreis Märkisch-Oderland in Brandenburg. Linsdorf ist eine französische Gemeinde mit Einwohnern (Stand ) im Département Haut-Rhin in der Region Grand Est (bis 2015 Elsass). Cartigny-l’Épinay ist eine französische Gemeinde mit Einwohnern (Stand ) im Département Calvados in der Region Normandie. Filipiñana ist ein philippinisch-britischer Spielfilm unter der Regie von Rafael Manuel aus dem Jahr 2020. Ausbeutung und Ausgrenzung in den hierarchischen Strukturen der philippinischen Gesellschaft werden am Beispiel eines Golfclubs gezeigt. Das Schlangennest (engl. Titel: Whacking Day) ist die zwanzigste Folge der vierten Staffel der Serie Die Simpsons. Tłustoręby (deutsch Kirchberg) ist ein Dorf in der Gmina Niemodlin, im Powiat Opolski, der Woiwodschaft Oppeln im Südwesten von Polen. Die Schweizerische Gesellschaft für Organisation und Management (SGO) ist ein Verein mit Sitz in Zürich, Schweiz. Kleinkarlbach ist eine Ortsgemeinde im pfälzischen Landkreis Bad Dürkheim.
# Das Hempstead County ist ein County im US-Bundesstaat Arkansas.
# Die Gmina Abramów ist eine Landgemeinde im Powiat Lubartowski.

# Drei Bruchpiloten in Paris (Originaltitel: La Grande vadrouille), in Deutschland auch unter dem Titel Die große Sause bekannt, ist eine französische Filmkomödie, bei der Gérard Oury Regie führte und die 1966 in die Kinos kam.