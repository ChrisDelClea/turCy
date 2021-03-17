import os
import logging
import typing
import spacy
from spacy.tokens import Doc, Span, Token
from turcy.tree_dep_pattern import attach_triple2sentence
from spacy.language import Language

logging.basicConfig(level=logging.INFO)

Doc.set_extension('triples', default=[], force=True)
Span.set_extension('triples', default=[], force=True)
Token.set_extension('part', default=None, force=True)
Token.set_extension('posi', default=None, force=True)

def add_to_pipe(nlp):
    nlp.add_pipe("attach_triple2sentence", last=True)