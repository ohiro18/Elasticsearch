# -*- coding: utf-8 -*-
import re
import unicodedata

import nltk
from nltk.corpus import wordnet

import neologdn

import functools
from ja_sentence_segmenter.common.pipeline import make_pipeline
from ja_sentence_segmenter.concatenate.simple_concatenator import concatenate_matching
from ja_sentence_segmenter.normalize.neologd_normalizer import normalize
from ja_sentence_segmenter.split.simple_splitter import split_newline, split_punctuation

import pke

# 先にgccを入れるor最新版にする
# pip3 install --upgrade pip setuptools
# pip3 install -U nltk --user
# pip3 install neologdn
# pip3 install ja-sentence-segmenter
# pip3 install spacy==2.1.3
# pip3 install git+https://github.com/boudinfl/pke.git
# pip3 install "https://github.com/megagonlabs/ginza/releases/download/v1.0.2/ja_ginza_nopn-1.0.2.tgz"

# ln -s /usr/local/lib/python3.6/site-packages/en_core_web_sm  /usr/local/lib64/python3.6/site-packages/spacy/data/en
# ln -s /usr/local/lib64/python3.6/site-packages/spacy/lang/ja_ginza /usr/local/lib64/python3.6/site-packages/spacy/data/ja_ginza

def normalize(text):
    normalized_text = normalize_unicode(text)
    normalized_text = normalize_number(normalized_text)
    normalized_text = lower_text(normalized_text)
    normalized_text = text_normalizer(normalized_text)
    normalized_text = stopword(normalized_text)
    return normalized_text

def stopword(text):
    with open('japanese_stop_words.txt') as fd:
        stop_words = frozenset([line.rstrip(' ') for line in fd])
    return list(filter(lambda x: x not in stop_words, text))

def sentence_segmentation(text):
    split_punc2 = functools.partial(split_punctuation, punctuations=r"。!?")
    concat_tail_te = functools.partial(concatenate_matching, former_matching_rule=r"^(?P<result>.+)(て)$", remove_former_matched=False)
    segmenter = make_pipeline(normalize, split_newline, concat_tail_te, split_punc2)
    return segmenter(text)

def lower_text(text):
    return text.lower()

def text_normalizer(text):
    return neologdn.normalize(text)

def normalize_unicode(text, form='NFKC'):
    normalized_text = unicodedata.normalize(form, text)
    return normalized_text


def lemmatize_term(term, pos=None):
    if pos is None:
        synsets = wordnet.synsets(term)
        if not synsets:
            return term
        pos = synsets[0].pos()
        if pos == wordnet.ADJ_SAT:
            pos = wordnet.ADJ
    return nltk.WordNetLemmatizer().lemmatize(term, pos=pos)


def normalize_number(text):
    """
    pattern = r'\d+'
    replacer = re.compile(pattern)
    result = replacer.sub('0', text)
    """
    # 連続した数字を0で置換
    replaced_text = re.sub(r'\d+', '0', text)
    return replaced_text


speech2text = """
xxx
"""


pke.base.ISO_to_language['ja_ginza'] = 'japanese'

stopwords = list(ginza.STOP_WORDS)
nltk.corpus.stopwords.words_org = nltk.corpus.stopwords.words
nltk.corpus.stopwords.words = lambda lang: stopwords if lang == 'japanese' else nltk.corpus.stopwords.words_org(lang)

print("---------オリジナル-------------")
print(speech2text)

print("---------テキストクリーニング-------------")
print(list(normalize(speech2text)))

print("---------単語の分割-------------")
path = "list.txt"
with open(path) as f:
    l_strip = [s.strip() for s in f.readlines()]
    print(l_strip)

print("---------stopwords-------------")
with open('stop_word.txt', 'r', encoding='utf-8') as file:
    stop_words = [word.replace('\n', '') for word in file.readlines()]

lst = [x for x in l_strip if x not in stop_words]
print(lst)


