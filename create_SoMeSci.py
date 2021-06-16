# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
#%%

from articlenizer import formatting 
from rdflib import Graph, plugin, URIRef, Literal
from rdflib.serializer import Serializer
from rdflib.namespace import XSD, RDF, RDFS, FOAF
import json
import os
import copy


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
        "prov" : "http://www.w3.org/TR/prov-o/#",
        "comment": "http://www.w3.org/2000/01/rdf-schema#comment",
        "void": "http://rdfs.org/ns/void#",
        "dcterms" : "http://purl.org/dc/terms/",
        "foaf": "http://xmlns.com/foaf/0.1/",
        "schema" : "http://schema.org/",
        "dcat" : "http://www.w3.org/ns/dcat#"
    }



keywords = ["Scientific Articles","Corpus", "Software Mention","Named Entity Recognition","Relation Extraction","Entity Disambiguation","Entity Linking"]

# Mapping from software labels to KG class label
software = { 
    'Application' : 'sms:Application', # software
    'PlugIn' : 'sms:PlugIn', # plug-in
    'ProgrammingEnvironment' : 'sms:ProgrammingEnvironment', # programming language
    'OperatingSystem' : 'sms:OperatingSystem', # operating system
#    'web' : 'wd:Q193424', #web service 
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

           # 'web_usage' : [ software['web'],mention['usage']],
           # 'web_creation' : [ software['web'], mention['creation']],
           # 'web_mention' : [software['web'], mention['allusion']],
           # 'web_deposition' : [ software['web'], mention['deposition']],

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

phrase_map = {'Application_Usage' : "nif:Phrase",
            'Application_Creation' : "nif:Phrase",
            'Application_Mention' : "nif:Phrase",
            'Application_Deposition' : "nif:Phrase",
            
            'OperatingSystem_Usage' : "nif:Phrase",
            'OperatingSystem_Creation' : "nif:Phrase",
            'OperatingSystem_Mention' : "nif:Phrase",
            'OperatingSystem_Deposition' : "nif:Phrase",
            
            'ProgrammingEnvironment_Usage' : "nif:Phrase",
            'ProgrammingEnvironment_Creation' : "nif:Phrase",
            'ProgrammingEnvironment_Mention' : "nif:Phrase",
            'ProgrammingEnvironment_Deposition' : "nif:Phrase",
            
            'PlugIn_Usage' : "nif:Phrase",
            'PlugIn_Creation' : "nif:Phrase",
            'PlugIn_Mention' : "nif:Phrase",
            'PlugIn_Deposition' : "nif:Phrase",

           # 'web_usage' : [ software['web'],mention['usage']],
           # 'web_creation' : [ software['web'], mention['creation']],
           # 'web_mention' : [software['web'], mention['allusion']],
           # 'web_deposition' : [ software['web'], mention['deposition']],

            'SoftwareCoreference_Deposition' : "nif:Phrase",

            'Abbreviation' : 'nif:Phrase', # abbreviation
            'Developer' : 'nif:Phrase', #publisher
            'Extension' : 'nif:Phrase', # special edition
            'AlternativeName' : 'nif:Phrase', 
            'Citation' : 'nif:Phrase', # reference
            'Release' : 'nif:Phrase', # software release
            'URL' : 'nif:Phrase', # Uniform Resource Locator
            'Version' : 'nif:Phrase', # software version
            'License' : 'nif:Phrase' # licence
}

# mapping of relations to wikidata properties
# note that relations are inverted here
relation_map = {
            'Abbreviation_of' : 'sms:refersTo',
            'Developer_of' : 'sms:refersTo',
            'Extension_of' : 'sms:refersTo',
            'AlternativeName_of' : 'sms:refersTo', # official name
            'PlugIn_of' : 'sms:refersTo',
            'Citation_of' : 'sms:refersTo',
            'Release_of' : 'sms:refersTo',
            'Specification_of' : 'sms:refersTo',
            'URL_of' : 'sms:refersTo', # URL
            'Version_of' : 'sms:refersTo', # software version identifier
            'License_of' : 'sms:refersTo'
}

inv_relation_map = {
            'Abbreviation_of' : 'sms:referredToByAbbreviation',
            'Developer_of' : 'sms:referredToByDeveloper',
            'Extension_of' : 'sms:referredToByExtension',
            'AlternativeName_of' : 'sms:referredToByAlternativeName', # official name
            'PlugIn_of' : 'sms:referredToByPlugIn',
            'Citation_of' : 'sms:referredToByCitation',
            'Release_of' : 'sms:referredToByRelease',
            'Specification_of' : 'sms:referredToBySpecification',
            'URL_of' : 'sms:referredToByURL', # URL
            'Version_of' : 'sms:referredToByVersion', # software version identifier
            'License_of' : 'sms:referredToByLicense'
}

link_entities = [
    #"abbreviation",
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


# add dataset meta data
dataset = URIRef("./")
g.add((dataset, RDF.type, URIRef("void:Dataset")))
g.add((dataset, RDF.type, URIRef("dcat:Resource")))
g.add((dataset,URIRef("dcterms:license"), URIRef("https://creativecommons.org/licenses/by/4.0/")))
g.add((dataset, URIRef("dcterms:title"), Literal("SoMeSci")))
g.add((dataset, URIRef("dcterms:description"), Literal("A 5 Star Open Data Goldstand Corpus of Software Mentions in Scientific Articles")))
for k in keywords:
    g.add((dataset, URIRef("dcat:keyword"), Literal(k)))
g.add((dataset, URIRef("dcat:landingPage"), URIRef("https://data.gesis.org/somesci/")))
g.add((dataset, URIRef("dcat:contactPoint"), URIRef("https://data.gesis.org/somesci/index.html#contact")))

for _,v in context.items():
    g.add((dataset, URIRef("void:vocabulary"), Literal(v)))

g.add((dataset, URIRef("void:feature"), URIRef("http://www.w3.org/ns/formats/JSON-LD")))
g.add((dataset, URIRef("void:sparqlEndpoint"), URIRef("https://data.gesis.org/somesci/sparql")))
g.add((dataset, URIRef("dcterms:issued"), Literal("2021-06-16T24:00:00",datatype=XSD.dateTime)))


      


# Add parts of the datasets
methods_dataset = URIRef("PLoS_Methods")
g.add((methods_dataset, RDF.type, URIRef("void:Dataset")))
g.add((methods_dataset, URIRef("dcterms:title"),Literal("PLoS methods")))
g.add((methods_dataset, URIRef("prov:wasDerivedFrom"), URIRef("https://doi.org/10.5281/zenodo.3715147")))
g.add((methods_dataset, URIRef("dcterms:description"),Literal("Contains methods sections from PLoS articles")))
g.add((dataset, URIRef("void:subset"), methods_dataset))


sentences_dataset = URIRef("PLoS_sentences")
g.add((sentences_dataset, RDF.type, URIRef("void:Dataset")))
g.add((sentences_dataset, URIRef("dcterms:title"),Literal("PLoS sentences")))
g.add((sentences_dataset, URIRef("prov:wasDerivedFrom"), URIRef("https://doi.org/10.5281/zenodo.3715147")))
g.add((sentences_dataset, URIRef("dcterms:description"),Literal("Contains individual sentences with software mentions from PLoS articles")))
g.add((dataset, URIRef("void:subset"), sentences_dataset))


pubmed_dataset = URIRef("Pubmed_fulltexts")
g.add((pubmed_dataset, RDF.type, URIRef("void:Dataset")))
g.add((pubmed_dataset, URIRef("dcterms:title"),Literal("Pubmed fulltexts")))
g.add((pubmed_dataset, URIRef("dcterms:description"),Literal("Contains fulltext articles randomly sampled from Pubmed Central")))
g.add((dataset, URIRef("void:subset"), pubmed_dataset))


creation_dataset = URIRef("Creation_sentences")
g.add((creation_dataset, RDF.type, URIRef("void:Dataset")))
g.add((creation_dataset, URIRef("dcterms:title"),Literal("Creation Sentences")))
g.add((creation_dataset, URIRef("dcterms:description"),Literal("Contains individual sentences with statements about the creation of software from Pubmed Central articles")))
g.add((dataset, URIRef("void:subset"), creation_dataset))


g.add((dataset, URIRef("dcterms:creator"),URIRef("https://www.orcid.org/0000-0003-4203-8851")))
g.add((URIRef("https://www.orcid.org/0000-0003-4203-8851"), RDF.type, URIRef("foaf:Person")))
g.add((URIRef("https://www.orcid.org/0000-0003-4203-8851"), URIRef("foaf:name"), Literal("David Schindler")))
g.add((URIRef("https://www.orcid.org/0000-0003-4203-8851"), URIRef("foaf:mbox"), Literal("mailto:david.schindler@uni-rostock.de")))
g.add((URIRef("https://www.orcid.org/0000-0003-4203-8851"), URIRef("schema:organisation"), URIRef("https://ror.org/03zdwsf69")))

g.add((dataset, URIRef("dcterms:creator"),URIRef("creator3")))
g.add((URIRef("creator3"), RDF.type, URIRef("foaf:Person")))
g.add((URIRef("creator3"), URIRef("foaf:name"), Literal("Stefan Dietze")))
g.add((URIRef("creator3"), URIRef("foaf:mbox"), Literal("stefan.dietze@gesis.org")))
g.add((URIRef("creator3"), URIRef("schema:organisation"), URIRef("https://ror.org/018afyw53")))
g.add((URIRef("creator3"), URIRef("schema:organisation"), URIRef("https://ror.org/024z2rq82")))

g.add((dataset, URIRef("dcterms:creator"),URIRef("creator2")))
g.add((URIRef("creator2"), RDF.type, URIRef("foaf:Person")))
g.add((URIRef("creator2"), URIRef("foaf:name"), Literal("Felix Bensmann")))
g.add((URIRef("creator2"), URIRef("foaf:mbox"), Literal("felix.bensmann@gesis.org")))
g.add((URIRef("creator2"), URIRef("schema:organisation"), URIRef("https://ror.org/018afyw53")))


g.add((dataset, URIRef("dcterms:creator"),URIRef("https://www.orcid.org/0000-0002-7925-3363")))
g.add((URIRef("https://www.orcid.org/0000-0002-7925-3363"), RDF.type, URIRef("foaf:Person")))
g.add((URIRef("https://www.orcid.org/0000-0002-7925-3363"), URIRef("foaf:name"), Literal("Frank Krüger")))
g.add((URIRef("https://www.orcid.org/0000-0002-7925-3363"), URIRef("foaf:mbox"), Literal("frank.krueger@uni-rostock.de")))
g.add((URIRef("https://www.orcid.org/0000-0002-7925-3363"), URIRef("schema:organisation"), URIRef("https://ror.org/03zdwsf69")))

g.serialize(format="json-ld", context=context, destination="somesci-metadata.jsonld")

g.parse("empty_graph.jsonld", format="json-ld")


# def nodes_from_plos_methods(g, filename):
#     doi, _ = os.path.splitext(os.path.basename(filename))
#     doi = doi.replace('_','/')
#     #print("Working on {}".format(doi))
#     doc_id = "https://doi.org/{}".format(doi)
#     return add_document_node(g, filename, doc_id, doi)

def get_ann_for_index(ann, beg, end):
    selected_entities = {}
    for k,v in ann['entities'].items():
        if v['beg'] >= beg and v['end'] <= end:
            selected_entities[k] = copy.deepcopy(v)
            selected_entities[k]['beg'] -= beg
            selected_entities[k]['end'] -= beg
        elif v['beg'] < beg and v['end'] < beg or v['beg'] > end and v['end'] > end:
            pass
        else:
            raise(RuntimeError("Entity error at {}: {}-{} vs {}-{}".format(k, v['beg'], v['end'], beg, end)))
    selected_relations = {}
    for k,v in ann['relations'].items():
        if v['arg1'] in selected_entities and v['arg2'] in selected_entities:
            selected_relations[k] = v
        elif v['arg1'] not in selected_entities and v['arg2'] not in selected_entities:
            pass
        else:
            raise(RuntimeError("Relation over two sentences"))
    return selected_entities, selected_relations   

def nodes_from_PMC_ID(g, filename,  sub_dataset):
    doi, _ = os.path.splitext(os.path.basename(filename))
    doi.replace('_','/')
    doc_id = "https://www.ncbi.nlm.nih.gov/pmc/articles/{}".format(doi)

    fn_ann = os.path.splitext(filename)[0] + ".ann"


    with open(filename, 'r') as text_file, open(fn_ann,'r') as ann_file: 
        text = text_file.read()
        ann = ann_file.read()

    doc_ent_rel = formatting.annotation_to_dict(ann)
    #print(doc_ent_rel)
    
    doc = URIRef(doi)
    sent_list = formatting.sentence_based_info(text, ann, process_unicode=False, replace_math=False, correct=False, corr_cite=False) 
    g.add((doc, RDF.type, URIRef("nif:Context")))
    g.add((doc, URIRef("nif:broaderContext"), URIRef(doc_id)))
    g.add((doc, URIRef("nif:isString"), Literal(text))) 
    g.add((doc, URIRef("schema:isPartOf"), sub_dataset)) 
    g.add((sub_dataset, URIRef("schema:hasPart"), doc))

    if len(text.strip()) == 0:
        warning("Empty text file: {}".format(filename))


    sent_nodes = {}
    
    start_idx = 0
    for sent_idx, sent in enumerate(sent_list):
        sent_id = "{}/sentence{}".format(doi, sent_idx)
        nsent = URIRef(sent_id)
        g.add((nsent, RDF.type, URIRef("nif:Context")))
        g.add((nsent, RDF.type, URIRef("nif:Sentence")))
        g.add((nsent, RDF.type, URIRef("nif:OffsetBasedString")))
#        g.add((nsent, URIRef("schema:isPartOf"), sub_dataset))
        g.add((nsent, URIRef("nif:broaderContext"), doc))
        g.add((nsent, URIRef("nif:beginIndex"), Literal(start_idx)))
        end_idx = start_idx + len(sent['string'])
        g.add((nsent, URIRef("nif:endIndex"), Literal(end_idx)))
        g.add((nsent, URIRef("nif:isString"), Literal(sent['string'])))

 
        for eid, entity in sent['entities'].items():
            #if "software_suggestion" == entity['label']:
            #    warning("Found invalid entity")
            #    continue

            nentity = URIRef("{}/{}".format(sent_id, eid))
            sent_nodes[eid] = nentity
            
            if not entity['label'] in phrase_map:
                warning("No phrase type defined for {}".format(entity['label']))
                continue
            else:
                g.add((nentity, RDF.type, URIRef(phrase_map[entity['label']])))
            
            #g.add((nentity, RDF.type, URIRef("nif:OffsetBasedString")))
            g.add((nentity, URIRef("nif:anchorOf"), Literal(entity['string'])))
            g.add((nentity, URIRef("nif:beginIndex"), Literal(entity['beg'])))
            g.add((nentity, URIRef("nif:endIndex"), Literal(entity['end'])))
            g.add((nentity, URIRef("nif:referenceContext"), URIRef(nsent)))
            
            classURLs = entity_map[entity['label']]
            for classURL in classURLs:
                g.add((nentity, URIRef("its:taClassRef"), URIRef(classURL)))

            # link to identities if available
            if not entity['label'] in link_entities:
                continue
            label0 = entity['label'].split('_')[0]

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
                #print("Found developer {} in document {}".format(entity['string'], doc_id))
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
        #print(relation)
        if relation['label'] not in relation_map:
            warning("Unkown Relation: {}".format(relation['label']))
            continue

        nsoftware = sent_nodes[relation['arg2']]
        ninfo = sent_nodes[relation['arg1']]
        predicate = relation_map[relation['label']]
        g.add((ninfo,URIRef(predicate), nsoftware))
        
        if relation['label'] not in inv_relation_map:
            warning("Unkown Relation: {}".format(relation['label']))
            continue
        predicate = inv_relation_map[relation['label']]
        g.add((nsoftware, URIRef(predicate), ninfo))
    return


# %%
from lxml import etree

def methods_titles_from_xml(files, xml_folder):
    sections = {}
    for filename in files:
        with open(filename,'r') as file:
            l = sum([len(ll) for ll in file.readlines()])
        
        id = os.path.splitext(os.path.basename(filename))[0]
        xml_file = os.path.join(xml_folder, id + ".nxml")
        with open(xml_file, 'r' ) as f:
            tree = etree.parse(f)
            sec_titles_nodes = tree.xpath("//body/sec/title")
            sec_titles = [t.text for t in sec_titles_nodes if "method" in t.text.lower()]
            if len(set(sec_titles)) != 1: #exact 1 methods sections, or at least all with the same name
                warning("No unique methods ({}, {}) section found in {}".format(len(sec_titles), sec_titles, xml_file)) 
            else:
                sections[id] = {sec_titles[0] : {'Begin' : 0,'End' : l}}
    return sections

def methods_from_src(files):
    sections = {}
    for filename in files:
        id = os.path.splitext(os.path.basename(filename))[0]
        src_file = os.path.splitext(filename)[0] + '.src'
        sections[id] = {}
        with open(filename,'r') as file, open(src_file, 'r') as src:
            txt_lines = file.readlines()
            src_lines = src.readlines()
        if len(txt_lines) != len(src_lines):
            warning("Length of file do not match ({}:{}) for {}".format(len(txt_lines),len(src_lines), filename))
            continue
        cursor = 0
        last_cursor = 0
        cur_section = None
        for idx, txt_line in enumerate(txt_lines):
            if cur_section and cur_section != src_lines[idx]:    
                sections[id][cur_section] = {'Begin' : last_cursor, 'End': cursor}
                last_cursor = cursor + 1
            cur_section = src_lines[idx].strip()
            cursor += len(txt_line)
    return sections

            
  


# %%
plos_methods = []
pubmed_fulltext = []
plos_sentences = []



path = os.path.join(path_f,"PLoS_methods")
plos_methods = [os.path.join(path,file) for file in os.listdir(path) if file.endswith(".txt")]
print(len(plos_methods))
#plos_methods_sections = methods_titles_from_xml(plos_methods, "../Annotation/XML/PLoS_methods/")


path = os.path.join(path_f,"Pubmed_fulltext")
pubmed_fulltext = [os.path.join(path,file) for file in os.listdir(path) if file.endswith(".txt")]
print(len(pubmed_fulltext))
#with open("../Annotation/KG/Pubmed_fulltext/section_overview.json",'r') as f:
#    pubmed_fulltext_sections = json.load(f)

path = os.path.join(path_f,"PLoS_sentences")
plos_sentences = [os.path.join(path, file) for file in os.listdir(path) if file.endswith(".txt")]
print(len(plos_sentences))
#plos_sentences_sections = methods_titles_from_xml(plos_sentences, "../Annotation/XML/PLoS_sentences/")


path = os.path.join(path_f,"Creation_sentences")
PMC_creation_sentences = [os.path.join(path, file) for file in os.listdir(path) if file.endswith(".txt") ]
print(len(PMC_creation_sentences))


for ps_doc in plos_sentences:
    c = nodes_from_PMC_ID(g, ps_doc, sentences_dataset)
for ps_doc in plos_methods:
    c = nodes_from_PMC_ID(g, ps_doc, methods_dataset)
for pm_doc in pubmed_fulltext:
   c = nodes_from_PMC_ID(g, pm_doc, pubmed_dataset)
for pm_doc in PMC_creation_sentences:
    nodes_from_PMC_ID(g, pm_doc, creation_dataset)

g.serialize(format="json-ld", context=context, destination="somesci.jsonld")
print("Got {} warnings".format(len(warnings)))


# %%
print("Number of triples in graph: {}".format(len(g)))


