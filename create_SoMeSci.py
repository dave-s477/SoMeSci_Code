from articlenizer import formatting 
from rdflib import Graph, plugin, URIRef, Literal
from rdflib.serializer import Serializer
from rdflib.namespace import XSD, RDF, RDFS
import json
import os
import csv

warnings = []

def warning(warn):
    print("Warning: {}".format(warn))
    warnings.append(warn)


# URLs for used vocabulary
context = {
    "@vocab" : "http://schema.org/",
    "@base" : "http://data.gesis.org/somesci/",
    "sms" : "http://data.gesis.org/somesci/",
    "nif" : "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#",
    "wd" : "http://www.wikidata.org/entity/",
    "its": "http://www.w3.org/2005/11/its/rdf#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "comment": "http://www.w3.org/2000/01/rdf-schema#comment"
}

keywords = ["Scientific Articles","Corpus", "Software Mention","Named Entity Recognition","Relation Extraction","Entity Disambiguation","Entity Linking"]

# Mapping from software labels to KG class label
software = { 
    'Application' : 'sms:Application', # software
    'PlugIn' : 'sms:PlugIn', # plug-in
    'ProgrammingEnvironment' : 'sms:ProgrammingEnvironment', # programming language
    'OperatingSystem' : 'sms:OperatingSystem', # operating system
    'depositionstatment' : 'sms:SoftwareCoreference', #coreference
}

# Mapping from mention labels to KG mention class types
mention = {
    'usage' : 'sms:Usage', # use
    'creation' : 'sms:Creation', # software development
    'allusion' : 'sms:Allusion', # allusion
    'deposition' : 'sms:Deposition', # publication
}

# Mapping of mixed annotation types to multiple types    
entity_map = {'Application_Usage' : [software['Application'], mention['usage'] ],
            'Application_Creation' : [software['Application'],mention['creation']],
            'Application_Mention' : [software['Application'],mention['allusion'] ],
            'Application_Deposition' : [software['Application'],mention['deposition']],
            
            'OperatingSystem_Usage' : [ software['OperatingSystem'],mention['usage']],
            'OperatingSystem_Creation' : [ software['OperatingSystem'],mention['creation']],
            'OperatingSystem_Mention' : [ software['OperatingSystem'],mention['allusion']],
            'OperatingSystem_Deposition' : [ software['OperatingSystem'],mention['deposition']],
            
            'ProgrammingEnvironment_Usage' : [ software['ProgrammingEnvironment'],mention['usage']],
            'ProgrammingEnvironment_Creation' : [ software['ProgrammingEnvironment'],mention['creation']],
            'ProgrammingEnvironment_Mention' : [ software['ProgrammingEnvironment'],mention['allusion']],
            'ProgrammingEnvironment_Deposition' : [ software['ProgrammingEnvironment'],mention['deposition']],
            
            'PlugIn_Usage' : [ software['PlugIn'],mention['usage']],
            'PlugIn_Creation' : [ software['PlugIn'], mention['creation']],
            'PlugIn_Mention' : [ software['PlugIn'], mention['allusion']],
            'PlugIn_Deposition' : [ software['PlugIn'],mention['deposition']],

            'SoftwareCoreference_Deposition' : [software['depositionstatment'], mention['deposition']],

            'Abbreviation' : ['sms:Abbreviation'], # abbreviation
            'Developer' : ['sms:Developer'], #publisher
            'Extension' : ['sms:Extension'], # special edition
            'AlternativeName' : ['sms:AlternativeName'], 
            'Citation' : ['sms:Citation'], # reference
            'Release' : ['sms:Release'], # software release
            'URL' : ['sms:URL'], # Uniform Resource Locator
            'Version' : ['sms:Version'], # software version
            'License' : ['sms:License'] # licence
}

# mapping of text labels to nif:phrase subclasses
phrase_map = {'Application_Usage' : "sms:SoftwarePhrase",
            'Application_Creation' : "sms:SoftwarePhrase",
            'Application_Mention' : "sms:SoftwarePhrase",
            'Application_Deposition' : "sms:SoftwarePhrase",
            
            'OperatingSystem_Usage' : "sms:SoftwarePhrase",
            'OperatingSystem_Creation' : "sms:SoftwarePhrase",
            'OperatingSystem_Mention' : "sms:SoftwarePhrase",
            'OperatingSystem_Deposition' : "sms:SoftwarePhrase",
            
            'ProgrammingEnvironment_Usage' : "sms:SoftwarePhrase",
            'ProgrammingEnvironment_Creation' : "sms:SoftwarePhrase",
            'ProgrammingEnvironment_Mention' : "sms:SoftwarePhrase",
            'ProgrammingEnvironment_Deposition' : "sms:SoftwarePhrase",
            
            'PlugIn_Usage' : "sms:SoftwarePhrase",
            'PlugIn_Creation' : "sms:SoftwarePhrase",
            'PlugIn_Mention' : "sms:SoftwarePhrase",
            'PlugIn_Deposition' : "sms:SoftwarePhrase",

            'SoftwareCoreference_Deposition' : "sms:SoftwarePhrase",

            'Abbreviation' : 'sms:AbbreviationPhrase', # abbreviation
            'Developer' : 'sms:SoftwareDeveloperPhrase', #publisher
            'Extension' : 'sms:SoftwareExtensionPhrase', # special edition
            'AlternativeName' : 'sms:SoftwareAlternativeNamePhrase', 
            'Citation' : 'sms:SoftwareCitationPhrase', # reference
            'Release' : 'sms:SoftwareReleasePhrase', # software release
            'URL' : 'sms:URLPhrase', # Uniform Resource Locator
            'Version' : 'sms:VersionPhrase', # software version
            'License' : 'sms:LicensePhrase' # licence
}

# mapping of relations to wikidata properties
# note that relations are inverted here
relation_map = {
            'Abbreviation_of' : 'sms:hasAbbreviation',
            'Developer_of' : 'sms:hasDeveloper',
            'Extension_of' : 'sms:Extension',
            'AlternativeName_of' : 'sms:hasAlternativeName', # official name
            'PlugIn_of' : 'sms:hasPlugIn',
            'Citation_of' : 'sms:hasCitation',
            'Release_of' : 'sms:hasRelease',
            'Specification_of' : 'sms:hasSpecification',
            'URL_of' : 'sms:hasURL', # URL
            'Version_of' : 'sms:hasVersion', # software version identifier
            'License_of' : 'sms:hasLicense'
}

# list of labels to be linked to external identities
link_entities = [
    "Developer",
    "License",
    "URL",
    'Application_Usage',
    'Application_Creation',
    'Application_Mention',
    'Application_Deposition',
            
    'OperatingSystem_Usage',
    'OperatingSystem_Creation',
    'OperatingSystem_Mention',
    'OperatingSystem_Deposition',
    
    'ProgrammingEnvironment_Usage',
    'ProgrammingEnvironment_Creation',
    'ProgrammingEnvironment_Mention',
    'ProgrammingEnvironment_Deposition',
            
    'PlugIn_Usage',
    'PlugIn_Creation',
    'PlugIn_Mention',
    'PlugIn_Deposition',
    "Citation"
]


path_l = 'SoMeSci/Linking'
path_f = 'SoMeSci'

# create map of software identities
software_links = {}
with open(os.path.join(path_l,'artifacts.json'),'r') as f:
    softwares = json.load(f)
for s in softwares:
    if s['paper_id'] not in software_links:
        software_links[s['paper_id']] = {}
    if s['sentence_id'] not in software_links[s['paper_id']]:
        software_links[s['paper_id']][s['sentence_id']] = []
    software_links[s['paper_id']][s['sentence_id']].append(s)

# map of citation identities
with open(os.path.join(path_l,"citations.json")) as fn_ref:
    l = json.load(fn_ref)
references = {}
for ref in l:
    if ref['paper_id'] not in references:
        references[ref['paper_id']] = {}
    references[ref['paper_id']][ref['mention']] = ref['links']

# map of developer entities
with open(os.path.join(path_l,"developer.json")) as fn_ref:
    l = json.load(fn_ref)
developer = {}
for dev in l:
    if dev['paper_id'] not in developer:
        developer[dev['paper_id']] = {}
    if dev['sentence_id'] not in developer[dev['paper_id']]:
        developer[dev['paper_id']][dev['sentence_id']] = []
    developer[dev['paper_id']][dev['sentence_id']].append(dev)

# map of license entities
with open (os.path.join(path_l,"license.json")) as fn_l:
    l = json.load(fn_l)
licenses = {}

for lic in l:
    if lic['paper_id'] not in licenses:
        licenses[lic['paper_id']] = {}
    if lic['sentence_id'] not in licenses[lic['paper_id']]:
        licenses[lic['paper_id']][lic['sentence_id']] = []
    licenses[lic['paper_id']][lic['sentence_id']].append(lic)

# create graph based with some predefined properties
g = Graph()
g.parse("empty_graph.jsonld", format="json-ld")


# add dataset meta data
dataset = URIRef("./")
g.add((dataset, RDF.type, URIRef("Dataset")))
g.add((dataset,URIRef("license"), URIRef("https://creativecommons.org/licenses/by/4.0/")))
g.add((dataset, URIRef("name"), Literal("SoMeSci")))
g.add((dataset, URIRef("description"), Literal("A 5 Star Open Data Goldstand Corpus of Software Mentions in Scientific Articles")))
for k in keywords:
    g.add((dataset, URIRef("keywords"), Literal(k)))

# Author David
g.add((dataset, URIRef("author"),URIRef("https://www.orcid.org/0000-0003-4203-8851")))
g.add((URIRef("https://www.orcid.org/0000-0003-4203-8851"), RDF.type, URIRef("Person")))
g.add((URIRef("https://www.orcid.org/0000-0003-4203-8851"), URIRef("name"), Literal("David Schindler")))
g.add((URIRef("https://www.orcid.org/0000-0003-4203-8851"), URIRef("email"), Literal("mailto:david.schindler@uni-rostock.de")))
g.add((URIRef("https://www.orcid.org/0000-0003-4203-8851"), URIRef("organisation"), URIRef("https://ror.org/03zdwsf69")))

# Author Felix
g.add((dataset, URIRef("author"),URIRef("StefanDietze")))
g.add((URIRef("StefanDietze"), RDF.type, URIRef("Person")))
g.add((URIRef("StefanDietze"), URIRef("name"), Literal("Stefan Dietze")))
g.add((URIRef("StefanDietze"), URIRef("email"), Literal("stefan.dietze@gesis.org")))
g.add((URIRef("StefanDietze"), URIRef("organisation"), URIRef("https://ror.org/018afyw53")))
g.add((URIRef("StefanDietze"), URIRef("organisation"), URIRef("https://ror.org/024z2rq82")))

# Author Stefan 
g.add((dataset, URIRef("author"),URIRef("FelixBensmann")))
g.add((URIRef("FelixBensmann"), RDF.type, URIRef("Person")))
g.add((URIRef("FelixBensmann"), URIRef("name"), Literal("Felix Bensmann")))
g.add((URIRef("FelixBensmann"), URIRef("email"), Literal("felix.bensmann@gesis.org")))
g.add((URIRef("FelixBensmann"), URIRef("organisation"), URIRef("https://ror.org/018afyw53")))

# Author Frank
g.add((dataset, URIRef("author"),URIRef("https://www.orcid.org/0000-0002-7925-3363")))
g.add((URIRef("https://www.orcid.org/0000-0002-7925-3363"), RDF.type, URIRef("Person")))
g.add((URIRef("https://www.orcid.org/0000-0002-7925-3363"), URIRef("name"), Literal("Frank Krüger")))
g.add((URIRef("https://www.orcid.org/0000-0002-7925-3363"), URIRef("email"), Literal("frank.krueger@uni-rostock.de")))
g.add((URIRef("https://www.orcid.org/0000-0002-7925-3363"), URIRef("organisation"), URIRef("https://ror.org/03zdwsf69")))

# Funding
g.add((dataset, URIRef("funding"), URIRef("299150580")))
g.add((URIRef("299150580"), RDF.type, URIRef("Grant")))
g.add((URIRef("299150580"), URIRef("funder"), URIRef("https://ror.org/018mejw64")))
g.add((URIRef("https://ror.org/018mejw64"), RDF.type, URIRef("Organisation")))
g.add((URIRef("https://ror.org/018mejw64"), URIRef("name"), Literal("Deutsche Forschungsgemeinschaft")))

# function to create nodes for plos articles
def nodes_from_plos_methods(g, filename):
    doi, _ = os.path.splitext(os.path.basename(filename))
    doi = doi.replace('_','/')
    #print("Working on {}".format(doi))
    doc_id = "https://doi.org/{}".format(doi)
    return add_document_node(g, filename, doc_id, doi)

# function to create nodes for pmc articles
def nodes_from_pubmed_fulltext(g, filename):
    doi, _ = os.path.splitext(os.path.basename(filename))
    doi.replace('_','/')
    #print("Working on {}".format(doi))
    doc_id = "https://www.ncbi.nlm.nih.gov/pmc/articles/{}".format(doi)
    return add_document_node(g, filename, doc_id, doi)

# function to create node based on annotated text file (*.{txt,ann})
def add_document_node(g, fn_txt, doc_id, doi):
    num_sent_with_labels = 0
    num_sent = 0
    fn_ann = os.path.splitext(fn_txt)[0] + ".ann"

    # both files
    with open(fn_txt, 'r') as text_file, open(fn_ann,'r') as ann_file: 
        text = text_file.read()
        ann = ann_file.read()
    # file empty, skip creating further nodes
    if len(text.strip()) == 0:
        warning("Empty text file: {}".format(fn_txt))
        return (0,0,0)

    # get preprocessed information from articlenizer package
    doc_ent_rel = formatting.annotation_to_dict(ann)
    
    # create node that holds the outer context for each document
    doc = URIRef(doi)
    sent_list = formatting.sentence_based_info(text, ann, process_unicode=False, replace_math=False, correct=False, corr_cite=False) 
    g.add((doc, RDF.type, URIRef("nif:Context")))
    g.add((doc, URIRef("nif:broaderContext"), URIRef(doc_id)))
    g.add((doc, URIRef("nif:isString"), Literal(text))) 
    sent_nodes = {}

    start_idx = 0
    # for each sentence in document
    for sent_idx, sent in enumerate(sent_list):

        # create node for sentence
        sent_id = "{}/sentence{}".format(doi, sent_idx)
        nsent = URIRef(sent_id)
        g.add((nsent, RDF.type, URIRef("nif:Context")))
        g.add((nsent, RDF.type, URIRef("nif:Sentence")))
        g.add((nsent, RDF.type, URIRef("nif:OffsetBasedString")))
        g.add((nsent, URIRef("nif:broaderContext"), doc))
        g.add((nsent, URIRef("nif:beginIndex"), Literal(start_idx)))
        end_idx = start_idx + len(sent['string'])
        g.add((nsent, URIRef("nif:endIndex"), Literal(end_idx)))
        g.add((nsent, URIRef("nif:isString"), Literal(sent['string'])))
        start_idx = end_idx + 1

        num_sent += 1
        if len(sent['entities']) > 0:
            num_sent_with_labels +=1
    
        for eid, entity in sent['entities'].items():

            nentity = URIRef("{}/{}".format(sent_id, eid))
            sent_nodes[eid] = nentity

            # get the particular nif:phrase subtype for this annotation type            
            if not entity['label'] in phrase_map:
                warning("No phrase type defined for {}".format(entity['label']))
                continue
            else:
                g.add((nentity, RDF.type, URIRef(phrase_map[entity['label']])))
            # create nif:phrase information
            g.add((nentity, URIRef("nif:anchorOf"), Literal(entity['string'])))
            g.add((nentity, URIRef("nif:beginIndex"), Literal(entity['beg'])))
            g.add((nentity, URIRef("nif:endIndex"), Literal(entity['end'])))
            g.add((nentity, URIRef("nif:referenceContext"), URIRef(nsent)))
            
            # get the particular class label from the mapping 
            classURLs = entity_map[entity['label']]
            for classURL in classURLs:
                g.add((nentity, URIRef("its:taClassRef"), URIRef(classURL)))

            # link to identities if available
            if not entity['label'] in link_entities:
                continue
            label0 = entity['label'].split('_')[0]

            # link the different types
            if label0 in software.keys():      
                if doc_id in software_links and sent_idx in software_links[doc_id]:
                    softwares = software_links[doc_id][sent_idx]
                    # sentence in doc in list
                    matches = [s for s in softwares if s['mention'] == entity['string'] and 
                    s['beg'] == entity['beg'] and 
                    s['end'] == entity['end']]

                    if len(matches) != 1:
                        warning("No unique ({}) match found for {}({}:{}) in {}".format(len(matches), entity['string'], entity['beg'], entity['end'],  doc_id))
                    elif not matches[0]['link'].startswith("http"):
                        g.add((nentity, URIRef("its:taIdentRef"), Literal(matches[0]['link'])))
                    else:
                        g.add((nentity, URIRef("its:taIdentRef"), URIRef(matches[0]['link'])))
                else:
                    warning("Did not find entity '{}' of type '{}' in sentence {} in linking list of {}".format(entity['string'], label0, sent_idx,  doc_id))
                    
            elif label0 == 'Developer':
                if doc_id in developer and sent_idx in developer[doc_id]:
                    developers = developer[doc_id][sent_idx]
                    # search for correct developer
                    matches = [d for d in developers if d['mention'] == entity['string'] and 
                    d['beg'] == entity['beg'] and 
                    d['end'] == entity['end']]
                    #print(matches)
                    if len(matches) != 1:
                        warning("No unique ({}) match found for {}({}:{}) in {}".format(len(matches), entity['string'], entity['beg'], entity['end'],  doc_id))
                    elif not matches[0]['link'].startswith('http'):
                        g.add((nentity, URIRef("its:taIdentRef"), Literal(matches[0]['link'])))
                    else:
                        g.add((nentity, URIRef("its:taIdentRef"), URIRef(matches[0]['link'])))
                else:
                    warning("Developer {} not found for document {}".format(entity['string'],doc_id))

            elif entity['label'] == 'Citation':
                if doc_id in references and entity['string'] in references[doc_id]:
                    refs = references[doc_id][entity['string']]
                    for ref in refs:
                        g.add((nentity, URIRef("its:taIdentRef"), URIRef(ref)))
                else:     
                    warning("Did not find reference '{}' in {}.".format(entity['string'], doc_id))
            elif entity['label'] == 'License':
                if doc_id in licenses and sent_idx in licenses[doc_id]:
                    
                    # search for correct licence
                    matches = [d for d in licenses[doc_id][sent_idx] if d['mention'] == entity['string'] and 
                    d['beg'] == entity['beg'] and 
                    d['end'] == entity['end']]    

                    if len(matches) != 1:
                        warning("No unique ({}) licence match found for {}({}:{}) in {}".format(len(matches), entity['string'], entity['beg'], entity['end'],  doc_id))
                        warning(sent)
                    elif not matches[0]['link'].startswith("http"):
                        g.add((nentity, URIRef("its:taIdentRef"), Literal(matches[0]['link'])))
                    else:
                        g.add((nentity, URIRef("its:taIdentRef"), URIRef(matches[0]['link'])))
                else:     
                    warning("Did not find licence '{}' in {}.".format(entity['string'], doc_id))
                
            elif entity['label'] == 'URL':
                url_link = entity['string']
                if not url_link.startswith("http"):
                    url_link = "http://{}".format(url_link)
                else:
                    g.add((nentity, URIRef("its:taIdentRef"), URIRef(url_link)))
            else:
                # entity is of type should be linked, but we have no map
                warning("Cannot link {}: {}".format(entity['label'], entity['string']))

    # finally, transfer relations from textual format for nif:inter based format
    for relation in doc_ent_rel['relations'].values():
        if relation['label'] not in relation_map:
            warning("Unkown Relation: {}".format(relation['label']))
            continue

        nsoftware = sent_nodes[relation['arg2']]
        ninfo = sent_nodes[relation['arg1']]
        predicate = relation_map[relation['label']]
        g.add((nsoftware,URIRef(predicate), ninfo))
    return (num_sent_with_labels, num_sent, len(sent_list))


# go through all documents of the respective sub groups

path = os.path.join(path_f,"PLoS_methods")
plos_methods = [os.path.join(path,file) for file in os.listdir(path) if file.endswith(".txt")]
print(len(plos_methods))

path = os.path.join(path_f,"Pubmed_fulltext")
pubmed_fulltext = [os.path.join(path,file) for file in os.listdir(path) if file.endswith(".txt")]
print(len(pubmed_fulltext))

path = os.path.join(path_f,"PLoS_sentences")
plos_sentences = [os.path.join(path, file) for file in os.listdir(path) if file.endswith(".txt")]
print(len(plos_sentences))

path = os.path.join(path_f,"Creation_sentences")
plos_creation_sentences = [os.path.join(path, file) for file in os.listdir(path) if file.endswith(".txt") and file.startswith("10.1371")]
print(len(plos_creation_sentences))

PMC_creation_sentences = [os.path.join(path, file) for file in os.listdir(path) if file.endswith(".txt") and file.startswith("PMC")]
print(len(PMC_creation_sentences))

sent_count = 0
sent_count2 = 0
sent_count_with_label = 0

for ps_doc in plos_sentences:
    c = nodes_from_plos_methods(g, ps_doc)
    sent_count_with_label += c[0]
    sent_count += c[1]
    sent_count2 += c[2]
for ps_doc in plos_methods:
    c = nodes_from_plos_methods(g, ps_doc)
    sent_count_with_label += c[0]
    sent_count2 += c[2]
    sent_count += c[1]
for ps_doc in plos_creation_sentences:
    c = nodes_from_plos_methods(g, ps_doc)
    sent_count_with_label += c[0]
    sent_count += c[1]
    sent_count2 += c[2]
for pm_doc in pubmed_fulltext:
    c = nodes_from_pubmed_fulltext(g, pm_doc)
    sent_count_with_label += c[0]
    sent_count += c[1]
    sent_count2 += c[2]
for pm_doc in PMC_creation_sentences:
    nodes_from_pubmed_fulltext(g, pm_doc)
    sent_count_with_label += c[0]
    sent_count += c[1]
    sent_count2 += c[2]

g.serialize(format="json-ld", context=context, destination="somesci.jsonld")
print("Got {} warnings".format(len(warnings)))
print("Of {} sentences, {} have labels".format(sent_count, sent_count_with_label))

print("Number of triples in graph: {}".format(len(g)))


