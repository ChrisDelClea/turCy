from typing import List
import json


class Pattern(dict):
    def __init__(self, tag_=None,
                 dep_=None,
                 lefts=None,
                 rights=None,
                 name=None,
                 keep=True,
                 appendOrder="inOrder",
                 part=None,
                 posi=None,
                 subj=None,
                 pred=None,
                 obj=None,
                 complete=None,
                 truth=0,
                 **entries):
        object.__init__(self)
        self.tag_ = tag_
        self.dep_ = dep_
        self.lefts = lefts if lefts is not None else []
        self.rights = rights if rights is not None else []
        self.name = name
        self.keep = keep
        self.appendOrder = appendOrder
        self.part = part
        self.posi = posi
        self.subj = subj
        self.pred = pred
        self.obj = obj
        self.complete = complete
        self.truth = truth
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
