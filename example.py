import spacy
import turcy

def example():
    nlp = spacy.load("de_core_news_lg", exclude=["ner"])
    nlp.max_length = 2096700
    turcy.add_to_pipe(nlp)  # apply/use current patterns in list
    pipeline_params = {"attach_triple2sentence": {"pattern_list": "small"}}
    doc = nlp("Nürnberg ist eine Stadt in Deutschland.", component_cfg=pipeline_params)
    for sent in doc.sents:
        print(sent)
        for triple in sent._.triples:
            (subj, pred, obj) = triple["triple"]
            print(f"subject:'{subj}', predicate:'{pred}' and object: '{obj}'")

if __name__ == '__main__':
    example()
