import os
import re
import json
import pandas as pd
import urllib.request
import pickle
import itertools
from itertools import islice

def save_data(data, file_name):
    path = os.path.dirname(os.path.realpath(__file__))
    with open(f'{path}/{file_name}.pickle', 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

# @st.cache(suppress_st_warning=True)
def load_data(file_name=None, path=None):
    # if ((file_name == None) and (path==None)):
        # dataset = load_dataset("wikipedia", '20200501.de', split='train')
        # titles = dataset["title"]
        # texts = dataset["text"]
        # glitter = zip(titles, texts)
        #  data = dict(glitter)
        # return data, titles, texts
    if ((file_name != None) and (path !=None)):
        with open(f'{file_name}.pickle', 'rb') as handle:
            data = pickle.load(handle)
            # return dataset
    elif ((file_name == None) and (path != None)):
        work_dir = os.path.dirname(os.path.realpath(__file__))
        file_dir = os.path.join(work_dir, path)
        with open(file_dir, 'rb') as handle:
            data = pickle.load(handle)
            # return dataset
    return data

#########
#########
#########
def save_jsonl(file, path_filename):
    """
    Write list of objects to a JSON lines file.
    """
    work_dir = os.path.dirname(os.path.realpath(__file__))
    file_dir = os.path.join(work_dir, path_filename)
    with open(f"{file_dir}", 'w', encoding="utf8") as outfile:
        for entry in file.items():
            json.dump(entry, outfile)
            outfile.write('\n')
    print('Wrote {} records to {}'.format(len(file), path_filename))

def save_json(data_dict, file_name=None, path=None):
    if ((file_name != None) and (path == None)):
        path = os.path.dirname(os.path.realpath(__file__))
        with open(f"{path}/{file_name}.json", 'w', encoding="utf8") as f:
            json.dumps(data_dict, indent=4)
    elif ((file_name == None) and (path != None)):
        work_dir = os.path.dirname(os.path.realpath(__file__))
        file_dir = os.path.join(work_dir, path)
        with open(f"{file_dir}", 'w', encoding="utf8") as f:
            json.dump(data_dict, f, indent=4)

def load_json(path=None, file_name=None):
    if ((file_name != None) and (path == None)):
        path = os.path.dirname(os.path.realpath(__file__))
        with open(f"{path}/{file_name}.json", encoding="utf8") as f:
                train_data = json.loads(f.read())
    elif ((file_name == None) and (path != None)):
        work_dir = os.path.dirname(os.path.realpath(__file__))
        file_dir = os.path.join(work_dir, path)
        with open(file_dir, encoding="utf8") as f:
            train_data = json.loads(f.read())
    return train_data

def split_dict_equally(input_dict, chunks=2):
    """
    Splits dict by keys. Returns a list of dictionaries.
    """
    return_list = [dict() for idx in range(chunks)]
    idx = 0
    for k,v in input_dict.items():
        return_list[idx][k] = v
        if idx < chunks-1:
            idx += 1
        else:
            idx = 0
    return return_list

def chunks(data, SIZE=10000):
    it = iter(data)
    for i in range(0, len(data), SIZE):
        yield {k:data[k] for k in islice(it, SIZE)}
