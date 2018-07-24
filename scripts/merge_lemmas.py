#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

""" ==================================================================
Oracc transcription comparator
Aleksi Sahala - 2017 - University of Helsinki


DESCRIPTION:

This script can be used as a simple aid to find inconsistencies in the
lemmatization in Oracc corpus. It will find words having same
transliteration but different lemmatizations, as well as lemmas
that have only minimal differences.

The output will be given as follows:

Babil (8)	Babili (7) | Babilu* (8)
Babili (7)	Babilim*** (1) | Babilu******** (8) | Bābili* (1)
Bābili (1)	Bābilu (1)
Babilu (8)	Babitu (1) | Bubilu (3) | Bābilu* (1)
Barsip (7)	Barsipa** (2)

Star symbols indicate how many common transliterations the lemmas
have, i.e. Barsip and Barsipa share two common spellings in the
cuneiform. This is a strong indicator that these lemmas should
be merged into one. Similarly, Babili, Babilim, Babilu, Bābili
and Bābilu should definitely be merged, because

Babil == Babilu AND Babili == Babilu, Babilim, Bābili AND
Babilu == Bābilu (i.e. all of the lemmas share common spellings)

Sometimes the results which do not have common spellings are not as
easy to interpret, and in many cases they show false cognates, as in

Aba (2)	    Aia (2) | Ara (3) | Saba (7)

This could be solved by applying phonological distance measures,
but such are not implemented into the present version of this script.


INPUT FORMAT:

Input file should be in .tsv format. Column 1: Frequency.
Column 2: lemma. Column 3: transliterations of the lemma separated
by commas and enclosed in square brackets, e.g.


      1 Asaniu	[{KUR}a-sa-ni-u₂]
      1 Ašarmu	[{iri}a-šar-mu-um{ki}]
     11 Asdudu	[{URU}as-du-di, {KUR}as-du-di, {URU}aš₂-du-du]
     ...


USAGE:

See last three lines of this source code.

================================================================== """

dictionary = {}

def read_file(fname, format_):
    """ Read input file formatted as described above """
    ddict = {}
    print('reading file %s...' %fname)
    with open(fname, 'r', encoding="utf-8", errors="ignore") as f:
        if format_ == 'freq':
            for l in f.read().splitlines():
                l = l.strip()
                freq = int(re.sub('^(\d+?).+', r'\1', l))
                lemma = re.sub('[0-9 ]', '', l.split('\t')[0])
                xlit = l.split('\t')[1][1:-1].split(', ')
                ddict[lemma] = [freq, xlit]
            return ddict
        else:
            for l in f.read().splitlines():
                ddict[l] = [0, []]
            return(ddict)
            

def write_file(fname, content):
    with open(fname, "w", encoding="utf-8") as local_file:
        local_file.write(content)

def score_strings(w1, w2):
    """ Use Hamming distance for strings of equal length
    and Levenshtein for those of different length """
    if len(w1) == len(w2):
        return hamming(w1.lower(), w2.lower())
    else:
        return levenshtein(w1.lower(), w2.lower())

def count_comparisons(d):
    """ Count the number of comparisons """
    i, j = 1, 1
    while i < d:
        i += 1
        j += i
    return j

def get_freq(lemmas, show_freqs):
    """ Get frequencies for each lemma """
    if show_freqs:
        res = []
        for l in lemmas:
            freq = data[re.sub('[–\* \?\[\]0-9]', '', l)][0]
            res.append('%s (%i)' % (l, freq))
        return res
    else:
        return lemmas

def f_xlit(x):
    x = re.sub('\{URU\}|\{KUR\}|\{KI\}|[₁₂₃₄₅₆₇₈₉₀]', '', x.lower())
    x = re.sub('\.', '-', x.lower())
    x = re.sub('\(|\)', '', x)
    x = re.sub('ŋ', 'g', x)
    return x
    
def compare_xlits(target, suggestions):
    """ Compare lemmas by their transliteration """
    t_xlits = data[target][1]
    s_dict = {}
    for s in suggestions:
        s_xlits = data[s][1]
        for t in t_xlits:
            if f_xlit(t) in [f_xlit(z) for z in s_xlits]:
                if s not in s_dict.keys():
                    s_dict[s] = '*'
                else:
                    s_dict[s] += '*'
            else:
                if s not in s_dict.keys():
                    s_dict[s] = ''
                    
    return ['%s%s' % (x, s_dict[x]) for x in s_dict.keys()]

def compare(dict_data):

    data = list(dict_data.keys())
    print('%i entries, %i comparisons'\
          % (len(data), count_comparisons(len(data))))
    m = range(0, len(data), int(len(data)/100))
    
    for w1 in data:
        index = data.index(w1)

        """ Print progress """
        if index in m:
            print('%i / %i' % (index, len(data)))
            
        for w2 in data[index+1:]:
            x = sorted([len(w1), len(w2)])
            if x[1] - x[0] > 3:
                pass
            else:                    
                score = score_strings(w1, w2)

                if len(w1) >= 8:
                    min_val = 2
                else:
                    min_val = 1

                if score <= min_val:
                    if w1 not in dictionary.keys():
                        dictionary[w1] = [w2]
                    else:
                        dictionary[w1].append(w2)
                        #print("%i; %s; %s" % (score, w1, w2))

def hamming(s1, s2):
    return sum(e1 != e2 for e1, e2 in zip(s1, s2))

def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def merge_entries(dic):
    for key in dic.keys():
        for val in dic[key]:
            if val in dic.keys():
                dic[key] += dic[val]
                dic[val] = '_'

def print_results(show_freqs):
    #merge_entries(dictionary)
    for k in dictionary.keys():
        if dictionary[k] == '_':
            pass
        else:
            if '_' in dictionary[k]:
                results = list(filter(lambda x: x!= '_', dictionary[k]))
            else:
                results = dictionary[k]
        
            filt_res = compare_xlits(k, results)
            #print(filt_res, results)
            print('%s\t\t\t%s' % (get_freq([k], show_freqs)[0],\
                              ' | '.join(sorted(list(set(
                                  get_freq(filt_res, show_freqs)))))))

data = read_file('places_with_translit.txt', 'freq')
compare(data)
print_results(True)
