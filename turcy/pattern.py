from typing import List
import json


class Pattern(dict):
    def __init__(self, tag, dep=None, lefts=None, rights=None, name=None, keep=True, appendOrder="inOrder", **entries):
        object.__init__(self)
        self.tag_ = tag
        self.dep_ = dep
        self.lefts = lefts if lefts is not None else []
        self.rights = rights if rights is not None else []
        self.name = name
        self.keep = keep
        self.appendOrder = appendOrder  # Pre-order #https://medium.com/odscjournal/binary-search-tree-implementation-in-python-5f8a50341eaf
        # self.__dict__.update(entries)

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        if name == "lefts" or name == "rights":
            self[name] = []
            for val in value:
                self[name].append(Pattern(**val))
        else:
            self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __str__(self):
        return f"{{'tag':'{self.tag_}','dep':'{self.dep_}'}}"

    def __repr__(self):
        return f"{{'tag':'{self.tag_}','dep':'{self.dep_}'}}"
