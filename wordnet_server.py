""
import BaseHTTPServer
import time
import sys
import urlparse
from nltk.corpus import wordnet as wn
import json
import inflect
import re
import urllib

HOST_NAME = 'localhost' # !!!REMEMBER TO CHANGE THIS!!!
PORT_NUMBER = 9111 # Maybe set this to 9000.
oneGrams = {}
twoGrams = {}

def noDup(listy):

    x = listy
    x = list(set(x))
    return x

def get_synonyms(word):

    
    pluralizer = inflect.engine()

    syn_set = []
    wnsynset = wn.synsets(word)


    for i in range(0, len(wnsynset)):
        
        for lemma in wnsynset[i].lemma_names():

            syn_set.append(lemma.lower())
            
# adds plurals and removes dups
    
    syn_setnodup = []
    for item in syn_set:
        if item not in syn_setnodup:
            syn_setnodup.append(item)

    syn_set_final = []
    for item in syn_setnodup:
        syn_set_final.append(item)
        syn_set_final.append(pluralizer.plural(item))

    
    return syn_set_final

def get_singplu(word):

    syn_set = []
    pluralizer = inflect.engine()


    if len(word.split()) == 1:
        wnsynset = wn.synsets(word)
        print wnsynset
        #for it in wnsynset:
        it = wnsynset[-1]
        print it.lemma_names()
        

        if word.lower() in it.lemma_names():
            print "IT IS SINGULAR"
            return [word, pluralizer.plural(word)]
        
        #for i in range(0, len(wnsynset)):
         #   for lemma in wnsynset[i].lemma_names():
        #      syn_set.append(lemma)
        

        #if wnsynset:
            #for it in syn_set:
        else:
            print "IT IS PLURAL"
            sing = str(it.lemma_names()[0])
            plu = word
            return [sing, word]

        return [word, word]

    else:

        
        temp = word.split()[-1]
        others = " ".join(word.split()[0:-1])
        wnsynset = wn.synsets(temp)
        print "WNSYNSET" + str(wnsynset)
        print "MULTIWORD"


        #for it in wnsynset:
        #going to take first word in synset

        if wnsynset:
            it = wnsynset[-1]
            if temp in it.lemma_names():
                print it.lemma_names()
                print "IT IS SINGULAR"
                sing = others + " " + temp
                print "PLURAL IS" + str(temp)
                plu = others + " " + pluralizer.plural(temp)
                print "PLURAL IS" + str(plu)
                return [sing, plu]
            
            #for i in range(0, len(wnsynset)):
            #   for lemma in wnsynset[i].lemma_names():
            #       syn_set.append(lemma)
          
            #if wnsynset:
                #for it in syn_set:
            #if pluralizer.plural(wnsynset[-1]) == temp:
            else:
                print "IT IS PLURAL"
                sing = others + " " + str(it.lemma_names()[0])
                print "SING IS" + str(sing)
                plu = others + " " + temp
                print "PLURAL IS" + str(temp)
                return [sing, plu]

        
        return [word, word]


def get_antonym(word):

    print "Antonym for: " + word

    if len(word.split()) > 1:
        word = word.replace(" ","_")

    # the slow part
    wnsynset = wn.synsets(word)

    print "WYNSET" + str(wnsynset)
    antonym = None
    # only getting one antonym
    for i in wnsynset:
        for el in i.lemmas():
            x = el.antonyms()
            if len(x) > 0:
                print "Antonym"
                antonym = x[0].name()
                break
    syn_set = []
    if antonym is not None:
        print "synonyms for antonym " + str(antonym)


        if len(antonym.split()) > 1:
            word = antonym.replace(" ","_")

       

        # the slow part
        wnsynset = wn.synsets(antonym)

        print "WYNSET" + str(wnsynset)

        for i in range(0, len(wnsynset)):
            for lemma in wnsynset[i].lemma_names():
                print "LEMMA"
                print lemma
                
                syn_set.append(lemma)


                deriv = wn.lemma(wnsynset[i].name() +"."+ lemma)
                print "DERIVATIONS"
                for x in deriv.derivationally_related_forms():
                    print x.name
                    syn_set.append(x.name())

            print "Hyponym function: " 
            for hypo in wnsynset[i].hyponyms():
                syn_set.append(re.findall(r"[a-zA-Z]*",hypo.name())[0])
                print re.findall(r"[a-zA-Z]*",hypo.name())[0]

            '''
            print "Hypernym function: " 
            for hyper in wnsynset[i].hypernyms():
                syn_set.append(re.findall(r"[a-zA-Z]*",hyper.name())[0])
                print re.findall(r"[a-zA-Z]*",hyper.name())[0]
            '''

    return syn_set

     
def get_semantic_score(word):

    print "STARTING semanticScore for" + word

    if len(word.split()) > 1:
        word = word.replace(" ","_")

    pluralizer = inflect.engine()

    syn_set = []

    # the slow part
    wnsynset = wn.synsets(word)

    print "WYNSET" + str(wnsynset)

    syn_set_final = []
    # not suitable for synonyms but good for relations
    abstractions = []


    for i in range(0, len(wnsynset)):

        
        for lemma in wnsynset[i].lemma_names():
            print "LEMMA"
            print lemma
            
            syn_set.append(lemma)

            
            deriv = wn.lemma(wnsynset[i].name() +"."+ lemma)
        
            print "DERIVATIONS"
            for x in deriv.derivationally_related_forms():
                print x.name()
                syn_set.append(x.name())

    syn_set_b = noDup(syn_set)

    if len(syn_set_b) < 11:
        print "FULL SYNONYMS INCLUDING ABSTRACTIONS"
        print syn_set_b
        
    for i in range(0, len(wnsynset)):
        print "Hypernym function: " 
        for hyper in wnsynset[i].hypernyms():

            # 15 in random - did it for fund to finance
            hyper = re.findall(r"[a-zA-Z]*",hyper.name())[0]
            if len(syn_set_b) > 10:

                abstractions.append(hyper)
            else:
                

                syn_set.append(hyper)
            print hyper
        
        print "Hyponym function: " 
        for hypo in wnsynset[i].hyponyms():
            hypo = re.findall(r"[a-zA-Z]*",hypo.name())[0]
            if len(syn_set_b) > 10:
                abstractions.append(hypo)
            else:
               
                syn_set.append(hypo)
            print hypo
        

        # adds plurals and removes dups
    
    syn_setnodup = noDup(syn_set)
    syn_set_final = []
    for item in syn_setnodup:
        syn_set_final.append(item.lower())
        syn_set_final.append(pluralizer.plural(item).lower())
    

    abstractions = noDup(abstractions)
    abstractions_final = []
    for item in abstractions:
        abstractions_final.append(item.lower())
        abstractions_final.append(pluralizer.plural(item).lower())
    
    uselesswords = ["issues", "issues", "organization", "organizations"]
   
    abstractions_final = [w for w in abstractions_final if w.lower() not in uselesswords]
    syn_set_final = [w for w in syn_set_final if w.lower() not in uselesswords]


    print "END semanticScore"

    return [syn_set_final, abstractions_final]




def get_frequency(wordlist):
    popwords = {}

    for word in wordlist:
        print word
        if "(" in word:
            word = word.strip()[0:word.strip().find("(")]
        wordList = word.split(" ")
        try:
            if(len(wordList) == 1):
                popwords[oneGrams[wordList[0].lower()]] = word
            elif len(wordList) == 2:
                popwords[twoGrams[wordList[0].lower()+" "+wordList[1].lower()]] = word
    
        except:
            print "NO FREQ" + word
            continue

    return popwords

class RedirectHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_HEAD(s):
        s.do_GET()
    def do_GET(s):
        method_word = s.path[1:].split("/")

        print method_word
        ret = ""
        if method_word[0] == "Synonym":
            ret = get_synonyms(urllib.unquote(method_word[1]).decode('utf8'))
        if method_word[0] == "semanticscore":
            ret = get_semantic_score(urllib.unquote(method_word[1]).decode('utf8'))
        if method_word[0] == "singplu":
            ret = get_singplu(urllib.unquote(method_word[1]).decode('utf8'))
        if method_word[0] == "antonym":
            ret = get_antonym(urllib.unquote(method_word[1]).decode('utf8'))
        #if method_word[0] == "getfreq":
        #    ret = get_frequency(urllib.unquote(method_word[1]).decode('utf8'))

        s.send_response(200)
        s.send_header("content-type","application/json")
        s.end_headers()
        s.wfile.write(json.dumps(ret))
        s.wfile.close();           
    
    def do_OPTIONS(s):
	   s.do_GET()
    def do_POST(s):


        method_word = s.path[1:].split("/")

        
        content_len = int(s.headers.getheader('content-length', 0))
        post_body = s.rfile.read(content_len)
        
        post_body = urllib.unquote(post_body[9:]).decode('utf8')
        post_body = post_body.replace("+", " ")

        wordlist = eval(post_body)

        print method_word
   

        if method_word[0] == "getfreq":
            ret = get_frequency(wordlist)

        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        print json.dumps(ret)
        s.wfile.write(json.dumps(ret))
        # If someone went to "http://something.somewhere.net/foo/bar/",
        # then s.path equals "/foo/bar/".

        s.wfile.close()


if __name__ == '__main__':

    
    print "Loading word freq data..."
    oneGramFile = open("w1_.txt",'r').readlines()
    for line in oneGramFile:
        line = line.strip()
        [word,freq] = line.split("\t")
        oneGrams[word] = freq

    twoGramFile = open("w2_.txt",'r').readlines()
    for line in twoGramFile:
        line = line.strip()
        [freq,word1,word2] = line.split("\t")
        twoGrams[word1+" "+word2] = freq

    print "Data loaded..."
    
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), RedirectHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)