#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 29 21:34:35 2019

@author: Mei GAN
"""
import os
#créer un corpus
#le format du corpus est une liste qui contient des dictionnaires par phrase. 
#dans chaque dictionnaire des phrases, elle a plusieurs dictionnaires par mot.
def get_graphe():
    path_script= os.getcwd()
    path_fichier = path_script+"/fichiers/"
    files= os.listdir(path_fichier)
    corpus = []
    sentence = dict()
    for file in files: #lire tous les fichiers
        if not os.path.isdir(file): #si le fichier n'est pas un répertoire, on le prends
            with open(os.path.join(path_fichier,file), 'r') as raw_texte:
                for line in raw_texte:
                    if not line[:-1] and sentence: # supprimer le "\n" à la fin d'une ligne
                            corpus.append(sentence)
                            sentence = dict()
                    elif '#' in line and 'sent_id' in line: # mettre l'index de la phrase dans la dictionnaire
                        value = line.split('=')
                        sentence['id'] = value[1].replace('\n','')
                    elif '#' in line and 'text' in line: # mettre le texte dans la dictionnaire
                       value = line.split('=')
                       sentence['phrase'] = value[1].replace('\n','')
                    elif '#' not in line: #mettre l'index des mots et ses informations dans la dictionnaire
                        values = line[:-1].split('\t')
                        if '-' not in values[0]:
                            index='W'+ values[0]              
                            info_token = {}
                            info_token['form'] = values[1]
                            info_token['lemma'] = values[2]
                            info_token['cat'] = values[3]
                            info_token['dep'] = values[7]
                            info_token['head'] = 'W'+ values[6]
                            sentence[index] = info_token
    return corpus
        
'''
cette étape est de trouver le chemin entre keystart et keyend
keystart est l'index du mot (p.ex, 'W1' est l'index du permier mot d'une phrase)
keyend est l'index d'un autre mot
listeParentStart est une liste des têtes du keystart
listeParentEnd est une liste des têtes du keyend
'''
def find_path(sequence, keystart, keyend, listeParentStart=None,listeParentEnd=None):
    if listeParentStart == None:
        listeParentStart = []
    if listeParentEnd == None:
        listeParentEnd = [] 
        
# ajouter le keystart et le keyend dans des listes 
    if not listeParentStart and not listeParentEnd: 
        listeParentStart.append(keystart)
        listeParentEnd.append(keyend)
        
# si le parent/la têtes du keystart n'est pas 'W0', c'est-à-dire qu'il n'est pas le root de la phrase, on change le parent et l'ajoute dans la liste
# si le parent/la tête du keystart est 'W0', il est le root de la phrase. on ne l'ajoute pas et le parent est égale au keystart
    if sequence[keystart]['head'] != 'W0':
        parentStart = sequence[keystart]['head']
        listeParentStart.append(parentStart)
    else:
        parentStart = keystart
# le même pour le parent du keyend.
    if sequence[keyend]['head'] != 'W0':
        parentEnd = sequence[keyend]['head']
        listeParentEnd.append(parentEnd)
    else:
        parentEnd = keyend

# on compare les deux listes en faisant une intersection
# si l'intersection n'est pas vide, on a trouvé leur co-parent
# la liste du chemin contient deux parties ; l'une est du permier mot(start) au co-parent; l'autre est du co-parent au deuxième mot(end)
    if set(listeParentStart) & set(listeParentEnd):
        coparent = (set(listeParentStart) & set(listeParentEnd)).pop()
        indexCopStart = listeParentStart.index(coparent)
        indexCopEnd = listeParentEnd.index(coparent)
        return listeParentStart[:indexCopStart+1] + listeParentEnd[:indexCopEnd][::-1]
# si les parents des deux mot sont root, ils sont un même mot, donc il n'existe pas de chemin enter les deux mots.
    elif sequence[keystart]['head'] == 'W0' and sequence[keyend]['head'] == 'W0':
        return []
# sinon on fait encore une fois la fonction 
    else:
        return find_path(sequence, parentStart, parentEnd,listeParentStart,listeParentEnd)


# après trouver la chemin des parents, on va trouver leurs dépendances
def find_dep_path(sequence, path, attribute):
    dep_path = ''

# on ajoute le permier
    if path:
        if attribute == 'cat':
            dep_path = f"{sequence[path[0]]['form']}/{sequence[path[0]][attribute]}"
        elif attribute == 'lemma':
            dep_path = f"{sequence[path[0]]['form']}/{sequence[path[0]][attribute]}"
        else:
            dep_path = sequence[path[0]][attribute]
            
# on ajoute les restes
        keyprevious = path[0]
        for node in path[1:]:
            if attribute == 'cat':
                word = f"{sequence[node]['form']}/{sequence[node][attribute]}"
            elif attribute == 'lemma':
                word = f"{sequence[node]['form']}/{sequence[node][attribute]}"
            else:
                word = sequence[node][attribute]
            dep = sequence[node]['dep']
            head = sequence[node]['head']
            
# comme la liste des parents contient deux parties, la chemin des dépendances est aussi contient deux
# l'une partie est les flèches à gauche; l'autre est les flèches à droit. elles signifient qui est la relation des dépendances
            if head == keyprevious:
                dep_path += f" -[{dep}]-> {word}"
            else:
                dep_path += f" <-[{dep}]- {word}"
            keyprevious = node
    return dep_path

'''
cette épate est de trouver le chemin de dépendance enter les deux mots saisis
start : le permier mot/lemme/pos
end : le deuxieme mot/lemme/pos
attribute: form/lemma/cat
'''
def find_all_paths(corpus, start, end, attribute): 
    depPaths = []
    all_results = []
    id_phrase_paths = {}
    for sequence in corpus:
        keyStart = []
        keyEnd = []
        for key,value in sequence.items(): 
            if key not in ['id','phrase']:
                if start == value[attribute]:
                    keyStart.append(key) 
                elif end == value[attribute]:
                    keyEnd.append(key)
        if keyStart and keyEnd:
            id_phrase_paths = {}
            depPaths = []
            for ks in keyStart: 
                for ke in keyEnd: 
                    path = []
                    path = find_path(sequence,ks,ke) # aller à la fonction find_path
                    if path:
                        depPath = find_dep_path(sequence,path,attribute) # aller à la fonction find_dep_path
                        depPaths.append(depPath)
            if depPaths:
                id_phrase_paths['id'] = sequence['id']
                id_phrase_paths['phrase'] = sequence['phrase']
                id_phrase_paths['paths'] = depPaths
                all_results.append(id_phrase_paths)
                     
                        
    return all_results


corpus=get_graphe()
bienvenu = "Bienvenu au monde de dépendance. D'abord, choisissez la catégorie(form/lemma/cat), ensuite saisissez deux mots ou lemmes ou POS"
print(bienvenu )
attribute = input("Veuillez choisir la catégorie (form/lemma/cat)\n")
if attribute not in ['form','lemma','cat']:
    print("Erreur ! Votre saisie n'est pas correcte.")
else:
    start = input("le permier : ")
    end = input("le deuxieme : ")
    print('')
    
# obtenir les résultats
    result = find_all_paths(corpus,start,end,attribute)
    if result == []:
        print('Ne pas trouver le chemin.')
    else:
        print('Voici les résultats : \n')
        for item in result:
            for key,value in item.items():
                 print(f"{key} : {value}")
            print(f"*"*60)
    
    