# -*- coding: utf-8 -*-
import re
from pytagcloud.lang.stopwords import StopWords
from operator import itemgetter

def get_tag_counts(text1, text2):
    """
    Search tags in a given text. The language detection is based on stop lists.
    This implementation is inspired by https://github.com/jdf/cue.language. Thanks Jonathan Feinberg.
    """
    words1 = map(lambda x:x.lower(), re.findall(r'\w+', text1, re.UNICODE))
    words2 = map(lambda x:x.lower(), re.findall(r'\w+', text2, re.UNICODE))
    
    s = StopWords()     
    s.load_language(s.guess(words))
    
    counted = {}
    
    for word in words1:
        if not s.is_stop_word(word) and len(word) > 1:
            if counted.has_key(word):
                counted[word] += 1
            else: 
                counted[word] = 1

    for word in words2:
        if not s.is_stop_word(word) and len(word) > 1:
            if counted.has_key(word):
                counted[word] -= 1
            else: 
                counted[word] = -1
      
    return sorted(counted.iteritems(), key=itemgetter(1), reverse=True)
    