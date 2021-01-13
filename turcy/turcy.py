import os
import logging
import typing
import spacy
from spacy.tokens import Span, Doc
from turcy.tree_dep_pattern import attach_triple2sentence

logging.basicConfig(level=logging.INFO)

Doc.set_extension('triples', default=[], force=True)
Span.set_extension('triples', default=[], force=True)

# turcy Class takes text,

def extract(text:str, nlp):
    nlp = spacy.load("de_core_news_lg")
    lemma_lookup = nlp.vocab.lookups.get_table("lemma_lookup")
    lemma_lookup["Amtskollegen"] = "Amtskollege"
    lemma_lookup["Kanzlerin"] = "Kanzler"


def add_to_pipe(nlp):
    lemma_lookup = nlp.vocab.lookups.get_table("lemma_lookup")
    lemma_lookup["Amtskollegen"] = "Amtskollege"
    lemma_lookup["Kanzlerin"] = "Kanzler"
    nlp.add_pipe(attach_triple2sentence, last=True)
