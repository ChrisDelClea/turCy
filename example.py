import spacy
import turcy

def example():
    nlp = spacy.load("de_core_news_lg")
    turcy.add_to_pipe(nlp)
    doc = nlp("Nürnberg ist eine Stadt in Deutschland.")
    for sent in doc.sents:
        for triple in sent._.triples:
            (subj, pred, obj) = triple["triple"]
            print(f"subject:'{subj}', predicate:'{pred}' and object: '{obj}'")


if __name__ == '__main__':
    example()
