# **SoMeSci**: **So**ftware **Me**ntions in **Sci**entific Articles

**SoMeSci–A 5 Star Open Data Gold Standard Knowledge Graph of Software Mentions in Scientific Articles** by

David Schindler, Felix Bensmann, Stefan Dietze, and Frank Krüger

## Abstract of the paper
Knowledge about software used in scientific investigations is important for several reasons, for instance, to enable an understanding of provenance and methods involved in data handling.
However, software is usually not formally cited, but rather mentioned informally within the scholarly description of the investigation, raising the need for automatic information extraction and disambiguation. 
Given the lack of reliable ground truth data, we present SoMeSci---Software Mentions in Scientific Articles---a gold standard knowledge graph of software mentions in scientific articles. 
It contains high quality annotations (IRR: k=.82) of 3756 software mentions in 1367 articles. 
Besides the plain mention of the software, we also provide relation labels for additional information, such as the version, the developer, a URL or citations. 
Moreover, we distinguish between different types, such as application, plugin or programming environment, as well as different types of mentions, such as usage or creation.
To the best of our knowledge, SoMeSci is the most comprehensive corpus about software mentions in scientific articles, providing training samples for Named Entity Recognition, Relation Extraction, Entity Disambiguation, and Entity Linking.
Finally, we sketch potential use cases and provide baseline results for the different tasks.


This repository contains all data and source code to re-create the SoMeSci knowledge graph and to run the use cases.
To this end, it contains the following repositories as `git submodules`:

* [SoMeSci](https://github.com/dave-s477/SoMeSci/): manually gold standard annotated software mentions in scholarly articles 
* [SoMeNLP](https://github.com/dave-s477/SoMeNLP): implementation of the use cases for using the manually annotated software mentions as training set
(Note that both bring their own licenses)

In addition, this repository contains the file `create_SoMeSci.py`, to create the knowledge graph representation of the annotation.
To run the code the following steps have to be done:
* Get the sub modules `git submodule init --update`
* Install necessary packages `pip install -i requirements.txt`
* Run the code `python3 create_SoMeSci.py` 

The corpus and the resulting SoMeSci knowledge graph are published at Zenodo [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4701764.svg)](https://doi.org/10.5281/zenodo.4701764)

A hosted version of the Knowledge Graph with a SPARQL Endpoint and sample queries for analyses can be found at [https://data.gesis.org/somesci].



Shield: [![CC BY 4.0][cc-by-shield]][cc-by]

This work (but not the submodules) is licensed under a [Creative Commons Attribution 4.0 International
License][cc-by].

[![CC BY 4.0][cc-by-image]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-image]: https://i.creativecommons.org/l/by/4.0/88x31.png
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg
