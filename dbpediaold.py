import re
import requests
import sys
from bs4 import BeautifulSoup
import time
import operator
import json
import nltk
from nltk.collocations import *
from nltk import word_tokenize
from nltk import pos_tag
from nltk import wordpunct_tokenize
#from nltk.book import *
from nltk.stem import *
import pickle
import json
from collections import Counter
from nltk.corpus import wordnet as wn
import inflect
from requests import get
import cookielib
import requests
import os
#from nltk.tag.stanford import NERTagger

#os.environ["nerpath"] = "/home/ms/Documents/Yureeka/Django/Yureeka/puzzles/stanford-ner-2015-04-20/stanford-ner.jar"

#st = NERTagger('/home/ms/Documents/Yureeka/Django/Yureeka/puzzles/stanford-ner-2015-04-20/classifiers/english.all.3class.distsim.crf.ser.gz', os.environ.get("nerpath")) 



def noDup(listdup):
	noduplist = []
	for item in listdup:
		if item not in noduplist:
			noduplist.append(item)
	return noduplist

def Synonym(word):

	
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


def urify(word):

	return "http://dbpedia.org/page/" + word.lower().capitalize().replace(" ", "_")



def ScrapePage(word):

	if "http" in word:
		uri = word
	else:
		uri = "http://dbpedia.org/page/" + word.replace(" ", "_")

		dbkeyphrase_html = requests.get(uri,headers={"Accept":"text/html","User-Agent": "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1; .NET CLR 1.1.4322)"})
		
		if dbkeyphrase_html.status_code == 404:
			uri = "http://dbpedia.org/page/" + word.lower().capitalize().replace(" ", "_")
			dbkeyphrase_html = requests.get(uri,headers={"Accept":"text/html","User-Agent": "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1; .NET CLR 1.1.4322)"})

		if dbkeyphrase_html.status_code == 404:
			uri = uri.replace("-", "_")
			dbkeyphrase_html = requests.get(uri,headers={"Accept":"text/html","User-Agent": "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1; .NET CLR 1.1.4322)"})
			

		if dbkeyphrase_html.status_code == 404:
			uri = uri + "s"
			dbkeyphrase_html = requests.get(uri,headers={"Accept":"text/html","User-Agent": "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1; .NET CLR 1.1.4322)"})

		print uri

		if dbkeyphrase_html.status_code == 404:
			keyphrase_soup = None
			print "THERE IS NOT SUCH PAGE"
			return keyphrase_soup

	# if page is ambiguous
	
	dbkeyphrase_text = dbkeyphrase_html.content

	keyphrase_soup = BeautifulSoup(dbkeyphrase_text)

	disamblinks = keyphrase_soup.findAll("a", attrs={'rel':'dbpedia-owl:wikiPageDisambiguates'})
	
	if len(disamblinks) > 0:
		disambwords = []
		for link in disamblinks:
			disambwords.append(link.findAll(text = True)[1].strip(":").encode('utf-8'))
		return disambwords

	else:
	
		return [keyphrase_soup, uri]


def ScrapeCategoryPage(word):

	if "http" in word:
		uri = word
	else:
		uri = "http://dbpedia.org/page/Category:" + word.replace(" ", "_").capitalize()+"s"
	

	dbkeyphrase_html = requests.get(uri,headers={"Accept":"text/html","User-Agent": "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1; .NET CLR 1.1.4322)"})

	if dbkeyphrase_html.status_code == 404:
		uri = "http://dbpedia.org/page/Category:" + word.replace(" ", "_").lower().capitalize()
		dbkeyphrase_html = requests.get(uri,headers={"Accept":"text/html","User-Agent": "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1; .NET CLR 1.1.4322)"})
		

	if dbkeyphrase_html.status_code == 404:
		uri = uri.replace("-", "_")+"s"
		dbkeyphrase_html = requests.get(uri,headers={"Accept":"text/html","User-Agent": "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1; .NET CLR 1.1.4322)"})
		
	if dbkeyphrase_html.status_code == 404:
		uri = uri.replace("-", "_")
		dbkeyphrase_html = requests.get(uri,headers={"Accept":"text/html","User-Agent": "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1; .NET CLR 1.1.4322)"})
	
	print uri


	
	
	dbkeyphrase_text = dbkeyphrase_html.content

	keyphrase_soup = BeautifulSoup(dbkeyphrase_text)

	if dbkeyphrase_html.status_code == 404:
		return False
	else:
		return [keyphrase_soup, uri]


def tagme(text):

	payload = {'key': 'a83422612f1d2deb425b09a9a5db4b6a', 'text': text, 'lang':'en'}
	r = requests.post("http://tagme.di.unipi.it/tag", data=payload)

	x = json.loads(r.text)

	tags = []

	for i in range(0, len(x['annotations'])):
		if float(x['annotations'][i]['rho']) > .20:

			if x['annotations'][i]['spot'] not in tags:
				tags.append(x['annotations'][i]['spot'].capitalize())


	# remove weird words for queries (and maybe people in the future)

	annoyingwikipediawords = ["search", "navigation", "wikipedia", "citation needed", "improve this article", "adding citations to reliable sources"]
	for word in tags:
		for it in annoyingwikipediawords:
			if word.strip().lower() == it.strip().lower():
				tags.remove(word)
				break
	print "TAGGS" + str(tags)
	return tags

def wikipediaTags(word):

	soup = ScrapePage(word)

	if type(soup) is list:
		return soup
	else:
		
		if soup is not None:
			wikipedialink = soup.findAll("a", attrs={'rev':'foaf:primaryTopic'})[0]["href"]

			wikipage_html = requests.get(wikipedialink, allow_redirects=False)

			if "<span class=\"mw-headline\" id=\"In_fiction\">In fiction</span>" in wikipage_html.content:
				wikipage_text = wikipage_html.content[0:wikipage_html.content.find("id=\"In_fiction\"")]

			else:
				wikipage_text = wikipage_html.content[0:wikipage_html.content.find("id=\"References\"")]



			wikisoup = BeautifulSoup(wikipage_text)

			wikitext = []

			wikili = wikisoup.findAll("li") 
			wikili = filter(lambda x: x.attrs == {}, wikili)
			for item in wikili:
				
				if len(item.findAll("a")) > 0:
					y = item.findAll("a")[0].findAll(text = True)
					
					if len(y[0]) > 2:

						wikitext.append(y[0].strip().capitalize())
			print "PROBLEM" + str(wikitext)

			# getting first paragraph
			wikip = soup.findAll("span", attrs={'property':'dbpedia-owl:abstract', 'xml:lang':'en'})[0]
			
			## this does not currently work
			# find links in first paragraph
			'''
			wikia = []
			wikia= wikisoup.findAll("a")
			
			
			for a in wikia:
				if len(a.findAll(text = True)) > 0:
					y = a.findAll(text = True)[0]
					if len(y) > 2:

						try:
							if str(y).strip().capitalize() not in wikitext:
								wikitext.append(str(y).strip(). capitalize())
						except:
							print "STUPID ENCODING"
			'''

			# tag me of first paragraph

			fulltext = ""
			for text in wikip.findAll(text = True):
				
				if len(text) > 2:
					fulltext = fulltext + str(text.encode('utf-8')).strip()
				

			tagmewords = tagme(fulltext)
			for item in tagmewords:
				if item not in wikitext:
					wikitext.append(item)
			
			return wikitext

		else:

			return None


def ScrapeConcept(uri):

	dbconcept_html = requests.get(uri,headers={"Accept":"text/html","User-Agent": "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1; .NET CLR 1.1.4322)"})
	

	dbconcept_text = dbconcept_html.content


	concept_soup = BeautifulSoup(dbconcept_text)

	return concept_soup



def ScrapeCategoryOf(word):
		
	keyphrase_soup = ScrapePage(word)

	if keyphrase_soup is not None:

		# for ambiguous results

		if type(keyphrase_soup) is list:

			return keyphrase_soup
		
		else:

			keysubject_a = keyphrase_soup.findAll("a", attrs={'rel':'dcterms:subject'})

			categories = []

			for i in range(0,len(keysubject_a)):

				categories.append(re.findall(r"(?<=Category:)[^\"]*", str(keysubject_a[i]))[0].replace("_", " "))	
			

			return categories


	# for empty pages
	else:

		return None


def titleOfPage(word):

	keyphrase_soup = ScrapePage(word)

	header = keyphrase_soup.findAll("title")[0].findAll(text=True)
	title = re.findall(r"(?<=About: )[^\']*", str(header))

	return title
	

def conceptScrapeSubjectOf(Category):

	subjects = []

	conceptsoup = ScrapeCategoryPage(Category)[0]
	
	if type(conceptsoup) is not bool:
		concsubject_a = conceptsoup.findAll("a", attrs={'rev':'dcterms:subject'})

		for i in range(0,len(concsubject_a)):

			subjects.append(concsubject_a[i].findAll(text=True)[1].replace("_"," ").replace(":", ""))

	
	return subjects

def conceptScrapeBroaderOf(Category):


	subjects = []

	conceptsoup = ScrapeCategoryPage(Category)[0]

	if type(conceptsoup) is not bool:
		concsubject_a = conceptsoup.findAll("a", attrs={'rev':'skos:broader'})

		for i in range(0,len(concsubject_a)):

			subjects.append(concsubject_a[i].findAll(text=True)[1].replace(":","").replace("_", " "))

	return subjects


def conceptScrapeBroader(Category):


	subjects = []

	conceptsoup = ScrapeCategoryPage(Category)[0]
	
	if type(conceptsoup) is not bool:
		concsubject_a = conceptsoup.findAll("a", attrs={'rel':'skos:broader'})

		for i in range(0,len(concsubject_a)):

			subjects.append(concsubject_a[i].findAll(text=True)[1].replace(":",""))

	return subjects

def semanticScore(word):

	pluralizer = inflect.engine()

	syn_set = []

	wnsynset = wn.synsets(word)

	syn_set_final = []


	for i in range(0, len(wnsynset)):
		for lemma in wnsynset[i].lemma_names():
			
			syn_set.append(lemma)
			deriv = wn.lemma(wnsynset[i].name() +"."+ lemma)
			for x in deriv.derivationally_related_forms():
				syn_set.append(x.name())
		#print "Hypernym function: " 
		for hyper in wnsynset[i].hypernyms():
			syn_set.append(re.findall(r"[a-zA-Z]*",hyper.name())[0])
		#print "Hyponym function: " 
		for hypo in wnsynset[i].hyponyms():
			syn_set.append(re.findall(r"[a-zA-Z]*",hypo.name())[0])


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

def relate(cat, query, relatedcontext, othercontext):

	
	total = []

	cat = stopwordify(cat)

	querysyns = semanticScore(query)

	if semanticScore(cat):
		for el in semanticScore(cat):
			for it in querysyns:
				if it.lower().strip() == el.lower().strip():
					relatedcontext.append(cat)
					break

			if cat in relatedcontext:
				break

		if cat not in relatedcontext and cat not in othercontext:
			othercontext.append(cat)
	else:
		if cat.lower().strip() == query.lower().strip():
			relatedcontext.append(cat)
		elif cat not in othercontext:
			othercontext.append(cat)


def nerFilter(resultlist):
	'''

	# tried to use the website at some point
	text = "\n".join(resultlist)
	print text
	uri = "http://nlp.stanford.edu:8080/ner/classifier=english.muc.7class.distsim.crf.ser.gz&outputFormat=highlighted&preserveSpacing=true&input="+text+"%0D%0A&Process=Submit+Query"
	html = requests.get(uri)
	content = html.content
	print content

	soup = BeautifulSoup(content)
	'''
	#disamblinks = keyphrase_soup.findAll("a", attrs={'rel':'dbpedia-owl:wikiPageDisambiguates'})


	
	text = "\n".join(resultlist)

	splittext = text.split()
	#tags = st.tag(splittext)
	cleantags = []
		
	for tag in tags[0]:
		if tag[1] != "ORGANIZATION" and tag[1] != "PERSON":
			cleantags.append(tag[0])

	newtext = " ".join(cleantags)
	newresultlist = []

	for res in resultlist:
		if res in newtext:
			newresultlist.append(res)
	'''
	for res in resultlist:

		print "NER analysis for " + res
		nertags = st.tag(res.split())
		print nertags
		for ner in nertags[0]:
			tags.append(ner[1])
		print tags
		if "PERSON" in tags or "ORGANIZATION" in tags:

			print res + " removed"
			resultlist.remove(res)

	'''
	return newresultlist

# in order to remove weird things like "by" and "type"

def actual(word):

		if "by" in word:
			print "MATTTCHH"
			split = word.split("_")
			if "type" in split:
				word = split[0]
			elif "People" in split:
				word = split[2]
			else:
				word = word[0:word.find("by")]

		return word

def stopwordify(listy):
	print "STOP WORDIFYING"
	
	newlisty = []
	if type(listy) is list:
		for it in listy:
			newlisty.append(actual(it))

	else:
		newlisty = actual(listy)
		
	print "RESULT STOPWORD" + str(newlisty)
	return newlisty

#MAIN FUNCTION




def dbpedia(query):
	subqueries = []
	wikipediaterms = []
	subcats = []
	othercontext = []
	relatedcontext = []
	relatedcontextsubqueries = {}
	subcatsubqueries = {}
	results = {}
	category = False
	wikipediad = False
	uselesswords = ["armagh", "fiction", "television", "tv", "films", "redirects", "but not", "the word", "defunct", "relocated", "lists", "wikipedia"]
	stopwords = ["\'ve","\'re","\'ll","\'d",'vs.', "constantly", "leave", "n't", "'s", "a","a's","able","about","above","according","accordingly","across","actually","after","afterwards","again","against","ain't","all","allow","allows","almost","alone","along","already","also","although","always","am","among","amongst","an","and","another","any","anybody","anyhow","anyone","anything","anyway","anyways","anywhere","apart","appear","appreciate","appropriate","are","aren't","around","as","aside","ask","asking","associated","at","available","away","awfully","b","be","became","because","become","becomes","becoming","been","before","beforehand","behind","being","believe","below","beside","besides","best","better","between","beyond","both","brief","but","by","c","c'mon","c's","came","can","can't","cannot","cant","cause","causes","certain","certainly","changes","clearly","co","com","come","comes","concerning","consequently","consider","considering","contain","containing","contains","corresponding","could","couldn't","course","currently","d","definitely","described","despite","did","didn't","different","do","does","doesn't","doing","don't","done","down","downwards","during","e","each","edu","eg","eight","either","else","elsewhere","enough","entirely","especially","et","etc","even","ever","every","everybody","everyone","everything","everywhere","ex","exactly","example","except","f","far","few","fifth","first","five","followed","following","follows","for","former","formerly","forth","four","from","further","furthermore","g","get","gets","getting","given","gives","go","goes","going","gone","got","gotten","greetings","h","had","hadn't","happens","hardly","has","hasn't","have","haven't","having","he","he's","hello","help","hence","her","here","here's","hereafter","hereby","herein","hereupon","hers","herself","hi","him","himself","his","hither","hopefully","how","howbeit","however","i","i'd","i'll","i'm","i've","ie","if","ignored","immediate","in","inasmuch","inc","indeed","indicate","indicated","indicates","inner","insofar","instead","into","inward","is","isn't","it","it'd","it'll","it's","its","itself","j","just","k","keep","keeps","kept","know","knows","known","l","last","lately","later","latter","latterly","least","less","lest","let","let's","like","liked","likely","little","look","looking","looks","ltd","m","mainly","many","may","maybe","me","mean","meanwhile","merely","might","more","moreover","most","mostly","much","must","my","myself","n","name","namely","nd","near","nearly","necessary","need","needs","neither","never","nevertheless","new","next","nine","no","nobody","non","none","noone","nor","normally","not","nothing","novel","now","nowhere","o","obviously","of","off","often","oh","ok","okay","old","on","once","one","ones","only","onto","or","other","others","otherwise","ought","our","ours","ourselves","out","outside","over","overall","own","p","particular","particularly","per","perhaps","placed","please","plus","possible","presumably","probably","provides","q","que","quite","qv","r","rather","rd","re","really","reasonably","regarding","regardless","regards","relatively","respectively","right","s","said","same","saw","say","saying","says","second","secondly","see","seeing","seem","seemed","seeming","seems","seen","self","selves","sensible","sent","serious","seriously","seven","several","shall","she","should","shouldn't","since","six","so","some","somebody","somehow","someone","something","sometime","sometimes","somewhat","somewhere","soon","sorry","specified","specify","specifying","still","sub","such","sup","sure","t","t's","take","taken","tell","tends","th","than","thank","thanks","thanx","that","that's","thats","the","their","theirs","them","themselves","then","thence","there","there's","thereafter","thereby","therefore","therein","theres","thereupon","these","they","they'd","they'll","they're","they've","think","third","this","thorough","thoroughly","those","though","three","through","throughout","thru","thus","to","together","too","took","toward","towards","tried","tries","truly","try","trying","twice","two","u","un","under","unfortunately","unless","unlikely","until","unto","up","upon","us","use","used","useful","uses","using","usually","uucp","v","value","various","very","via","viz","vs","w","want","wants","was","wasn't","way","we","we'd","we'll","we're","we've","welcome","well","went","were","weren't","what","what's","whatever","when","whence","whenever","where","where's","whereafter","whereas","whereby","wherein","whereupon","wherever","whether","which","while","whither","who","who's","whoever","whole","whom","whose","why","will","willing","wish","with","within","without","won't","wonder","would","would","wouldn't","x","y","yes","yet","you","you'd","you'll","you're","you've","your","yours","yourself","yourselves"]


	

	
	# Always look at the category page if it exists

	if ScrapeCategoryPage(query) != False:

		

		catquery = conceptScrapeBroader(query)
		category = True
		uri = ScrapeCategoryPage(query)[1]


	elif type(ScrapePage(query)) is list:

		results["subqueries"] = []
		results["subcats"] = []
		results["relatedcats"] = []
		results["othercats"] = []
		results["subcatsubqueries"] = []
		results["relatedcontextsubqueries"] = []
		results["wikipediaterms"] = []
		results["disambiguate"] = ScrapePage(query)


		return results


	# If there are no results at all
	elif ScrapeCategoryOf(query) is None:
		
		results["subqueries"] = []
		results["subcats"] = []
		results["relatedcats"] = []
		results["othercats"] = []
		results["subcatsubqueries"] = []
		results["relatedcontextsubqueries"] = []
		results["wikipediaterms"] = []
		results["disambiguate"] = []


		return results


	else:
		uri = ScrapePage(query)[1]
		catquery = ScrapeCategoryOf(uri)


	# Now run the code
	query = query.replace("_", " ")


	if category == True:

		subjectof = conceptScrapeSubjectOf(uri)
		broaderof = conceptScrapeBroaderOf(uri)
		

		#subqueries = nerFilter(stopwordify(subjectof))
		subqueries = stopwordify(subjectof)
		
		#subcats = nerFilter(stopwordify(broaderof))
		subcats = stopwordify(broaderof)


		# analysing the categories of the query as a cat
		for cat in catquery:
			
			if len(query.split()) == 1:
				relate(cat.replace("_", " "), query, relatedcontext, othercontext)
			else:
				# had to this because categories would be two words like "Educational Institution"
				for q in query.split():
					if q.lower() not in stopwords:
						relate(cat.replace("_", " "), q, relatedcontext, othercontext)
		# for weird situations where the category is empty like Category:School
		
		if len(subqueries) == 0 and len(subcats) == 0:

			# in case the s is throwing off the results (like Homes, Home)
			if ScrapeCategoryPage("http://dbpedia.org/page/Category:" + query.replace("_", " ").capitalize()) != False:

				uri = "http://dbpedia.org/page/Category:" + query.replace("_", " ").capitalize()
				subjectof = conceptScrapeSubjectOf(uri)

				broaderof = conceptScrapeBroaderOf(uri)
				

				#subqueries = nerFilter(stopwordify(subjectof))
				subqueries = stopwordify(subjectof)
				
				#subcats = nerFilter(stopwordify(broaderof))
				subcats = stopwordify(broaderof)

				catquery = conceptScrapeBroader(uri)
				# analysing the categories of the query as a cat
				for cat in catquery:
					
					if len(query.split()) == 1:
						relate(cat.replace("_", " "), query, relatedcontext, othercontext)
					else:
						# had to this because categories would be two words like "Educational Institution"
						for q in query.split():
							if q.lower() not in stopwords:
								relate(cat.replace("_", " "), q, relatedcontext, othercontext)

			# treating it like it was a Page result

			else:
				uri = ScrapePage(query)[1]
				catquery = ScrapeCategoryOf(uri)
				


				for cat in catquery:
					if query.lower() in cat.lower():
						wikipediad = True

						subjectof = conceptScrapeSubjectOf(cat)
						broaderof = conceptScrapeBroaderOf(cat)
						

						#subqueries = nerFilter(stopwordify(subjectof))
						subqueries = stopwordify(subjectof)
						
						#subcats = nerFilter(stopwordify(broaderof))
						subcats = stopwordify(broaderof)

				
					else:
						if len(query.split()) == 1:
							relate(cat.replace("_", " "), query, relatedcontext, othercontext)
						else:
							for q in query.split():
								if q.lower() not in stopwords:
									relate(cat.replace("_", " "), q, relatedcontext, othercontext)
		

				#add queries from the wikipedia page if no where else to be found
			
				if wikipediad == False:
					
					print "SCRAPING WIKIPEDIA PAGE"

					#wikipediaterms = nerFilter(wikipediaTags(query))
					wikipediaterms = wikipediaTags(uri)

					wikipediad = True

	
	# if no category page


	else:
		for cat in catquery:
			if len(query.split()) == 1:
				relate(cat.replace("_", " "), query, relatedcontext, othercontext)
			else:
				for q in query.split():
					if q.lower() not in stopwords:
						relate(cat.replace("_", " "), q, relatedcontext, othercontext)
		# for weird 

			#add queries from the wikipedia page if no where else to be found
		
		if wikipediad == False:
			
				
			print "SCRAPING WIKIPEDIA PAGE"

			#wikipediaterms = nerFilter(wikipediaTags(query))
			wikipediaterms = wikipediaTags(uri)

			wikipediad = True




	# checking for useless words
	for item in relatedcontext:
		for word in uselesswords:
			if word in item.lower():
				relatedcontext.remove(item)

	# this was generating too many results
	'''
	for item in relatedcontext:
		x = conceptScrapeSubjectOf(item, "direct")
		if len(x) > 0:
			relatedcontextsubqueries[item] = x
	'''			
	for item in subcats:
		for word in uselesswords:
			if word in item.lower():
				subcats.remove(item)

	for item in subqueries:
		for word in uselesswords:
			if word in item.lower():
				subqueries.remove(item)

	for item in wikipediaterms:
		for word in uselesswords:
			if word in item.lower():
				wikipediaterms.remove(item)
	'''
	for item in subcats:
		x = conceptScrapeSubjectOf(item, "direct")
		if len(x) > 0:
			subcatsubqueries[item] = x

	'''
	

	# preparing the dictionary to result 

	
	results["subqueries"] = list(set(subqueries))
	results["wikipediaterms"] = list(set(wikipediaterms))
	results["subcats"] = list(set(subcats))
	results["relatedcats"] = list(set(relatedcontext))
	results["othercats"] = list(set(othercontext))
	results["subcatsubqueries"] = list(set(subcatsubqueries))
	results["relatedcontextsubqueries"] = list(set(relatedcontextsubqueries))
	results["disambiguate"] = []


	print results
	return results


#if len(sys.argv[1]) > 0:
#	dbpedia(sys.argv[1])


# Need to fix your related subqueries = diving should be related to competitive diving
### Need to fix disambiguations, like footsie for example
## issues with hyphens
## need to sort google cse results with include,exclude of extra keywords related to query
# Fix the character encoding
# can include navbox
#### exclude personal names from results
# Do tagme of whole text if wikipedias returns few results? See Entertainment in education
# need to add separate list for the subcat titles so they can become queries
# maybe add relatedcontextcats subcats??
# fix the links in the beginning, wikia
# add google as a default search if nothing is found
# add see also
# need to lematize in the search google.py babysitting and babysitter