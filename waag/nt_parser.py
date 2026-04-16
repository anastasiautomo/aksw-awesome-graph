from rdflib import Graph, Literal, Namespace, URIRef
from pathlib import Path

AKSW_TYPES = [
    "http://aksw.org/schema/FundedProject",
    "http://aksw.org/schema/OpenSourceProject",
    "http://aksw.org/schema/CommunityProject",
    "http://aksw.org/schema/DatasetProject",
    "http://aksw.org/schema/IncubatorProject",
    "http://aksw.org/schema/AlumniProject"
]

DOAP = Namespace("http://usefulinc.com/ns/doap#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
SIOC = Namespace("http://rdfs.org/sioc/ns#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

class NTParser:
    def __init__(self, file_path: Path, base_iri: str):
        self.file_path = Path(file_path)
        self.base_iri = base_iri

        self.source_graph = None
        self.filtered_graph = None

    def load(self):
        if not self.source_graph:
            self.source_graph = Graph()
            self.source_graph.parse(self.file_path, format="nt")
            print(f"Loaded AKSW graph: {len(self.source_graph)} triples")
        return self.source_graph

    def get_filtered_graph(self):
        if not self.filtered_graph:
            self.load()
            self.filtered_graph = Graph()

            for project in set(
                s for s, _, o in self.source_graph.triples((None, RDF.type, None))
                if str(o) in AKSW_TYPES
            ):

                github_urls = set()

                for _, _, url in self.source_graph.triples((project, FOAF.homepage, None)):
                    if str(url).startswith("https://github.com/AKSW"):
                        github_urls.add(url)

                for _, _, url in self.source_graph.triples((project, DOAP.browse, None)):
                    if str(url).startswith("https://github.com/AKSW"):
                        github_urls.add(url)

                for _, _, url in self.source_graph.triples((project, DOAP.repository, None)):
                    if str(url).startswith("https://github.com/AKSW"):
                        github_urls.add(url)

                if not github_urls:
                    continue

                # label
                label = None
                for _, _, lbl in self.source_graph.triples((project, RDFS.label, None)):
                    label = lbl
                    break

                # categories
                category_iris = []
                for _, _, o_type in self.source_graph.triples((project, RDF.type, None)):
                    if str(o_type) in AKSW_TYPES:
                        category_iri = URIRef(f"{self.base_iri}{o_type.split('/')[-1]}")
                        category_iris.append(category_iri)

                        self.filtered_graph.add((category_iri, RDF.type, SKOS.Concept))
                        self.filtered_graph.add((category_iri, RDFS.label, Literal(o_type.split('/')[-1])))

                # create github-based subjects
                for url in github_urls:
                    github_subject = URIRef(url)

                    self.filtered_graph.add((github_subject, RDF.type, DOAP.Project))
                    self.filtered_graph.add((github_subject, RDF.type, SIOC.Item))

                    self.filtered_graph.add((github_subject, OWL.sameAs, project))

                    if label:
                        self.filtered_graph.add((github_subject, RDFS.label, label))

                    for cat in category_iris:
                        self.filtered_graph.add((github_subject, DOAP.category, cat))

            print(f"Filtered graph: {len(self.filtered_graph)} triples")

        return self.filtered_graph
    