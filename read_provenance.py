import zipfile
from pathlib import Path
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD, DCTERMS
import json

# library to support visualisation of graphs
from rdflib.extras.external_graph_libs import rdflib_to_networkx_graph

# pyvis used to display the graphs
from pyvis.network import Network

# Namespaces
PROV = Namespace("http://www.w3.org/ns/prov#")
SCHEMA = Namespace("https://schema.org/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
PPLAN = Namespace("https://vocab.linkeddata.es/p-plan#")
CDIFPROV = Namespace("https://worldfair-project.eu/cdif/profiles/provenance/CDIF-PROV#")
CDIF4XAS = Namespace("https://worldfair-project.eu/cdif/profiles/cdif4xas/CDIF-4-XAS#")
PANET = Namespace("http://purl.org/pan-science/PaNET/")
SOSTDP = Namespace("http://sweetontology.net/propOrdinal/ProcessingLevel/")
EX = Namespace("http://example.org#")

file_formats = {"txt":"text/plain", "cif": "chemical/x-cif",
                "png":"image/png", "prj": "application/vnd.demeter.athena",
                "sp":"text/csv", "gds":"text/csv", "feffit":"text/plain", 
                "feff":"text/csv", "zip":"application/zip",
                "inp":"chemical/x-feff-input",
                "tabular": "text/plain",
                "xdi": "application/xdi",
                "h5": "application/x-hdf5",
                "nexus": "application/nexus",
                "jsonld": "application/ld+json"
               }

data_products = ["png"]

PANET_IDS={
    "XAS": PANET.PaNET01196, 
    "XAFS": PANET.PaNET01197, # subclass of XAS 
    "XANES":PANET.PaNET01199, # subclass of XAFS 
    "EXAFS": PANET.PaNET01198, # subclass of XAFS
    "Crystallograpic Study": PANET.PaNET2020063,
    "Crystallography":PANET.PaNET01082
    }

PROCESSING_LEVELS = {
    "raw": EX.Level0,
    "processed": SOSTDP.Level1,
    "transformed": SOSTDP.Level2,
    "derived": SOSTDP.Level3,
    "product": SOSTDP.Level4
}


# read file from zipped RO-Crate file
def get_file_from_rocratezip(zip_file, file_name):
    roc_zip_file = zipfile.ZipFile(zip_file)
    return roc_zip_file.open(file_name)
    
# Read the zipped crate and get main metadata file
def load_rocrate_metadata(crate_file):
    roc_zip_file = zipfile.ZipFile(crate_file)
    f = get_file_from_rocratezip(crate_file, "ro-crate-metadata.json")
    crate = json.load(f)
    return crate["@graph"]

#Return all JSON-LD entities of a given @type.
def find_entities(graph, type_name):
    return [e for e in graph if type_name in e.get("@type", [])]

#Convert RO-Crate IDs to URIs.
def to_uri(crate_base, entity_id):
    return URIRef(crate_base + entity_id)

#Convert json-ld crate to turtle
def crate_to_turtle(crate_path, save_path):
    g = Graph()
    roc_zip_file = zipfile.ZipFile(crate_path)
    f = roc_zip_file.open("ro-crate-metadata.json")
    g.parse(f,format="json-ld")
    out_ttl = Path(save_path, "ro-crate-metadata.ttl")
    print(f"saving to {out_ttl}")
    g.serialize(destination=out_ttl, format="turtle")

# get galaxy workflow file from RO-Crate
def get_workflow_json(ro_crate_zip):
    graph = load_rocrate_metadata(ro_crate_zip)
    roc_files = find_entities(graph, "File")
    workflow_file = ""
    for a in roc_files:
        if a['@id'][-3:] == ".ga" :
            workflow_file = a['@id']
            break    
    f = get_file_from_rocratezip(ro_crate_zip, workflow_file)
    wf_ga_json = json.load(f)
    return wf_ga_json

# get txt containing entities RO-Crate metadata:
# invocation, datasets, etc
def get_roc_json_part(ro_crate_zip, file_name):
    graph = load_rocrate_metadata(ro_crate_zip)
    roc_file = ""
    roc_all_files = find_entities(graph, "File")
    for a in roc_all_files:
        if file_name in a['@id']:
            roc_file = a['@id']
            break
    f = get_file_from_rocratezip(ro_crate_zip, roc_file) 
    file_json = json.load(f)
    return file_json

# data sets are mapped to history objects
def get_history_mapped_ds(datasets_json, history_mapping):
    ds_id = ""
    for ds in datasets_json:
        chain = ds.get("copied_from_history_dataset_association_id_chain", [])
        if history_mapping in chain or history_mapping == ds["encoded_id"]:
            ds_id = ds["encoded_id"]
    return ds_id

# link ds generator to corresponding wf step
def get_wf_step(ds_uri, a_graph):
    
    ds_label =  get_a_label(a_graph, ds_uri)
    ret_val = None
    # fetch steps have the ds_name as the label
    for an_activity, p, o in a_graph.triples((None, RDFS.label, Literal(ds_label))):
        ret_val = an_activity                
    return ret_val

# add custom labels to activities
def custom_labels(a_graph):
    for an_activity in a_graph.subjects(RDF.type, PROV.Activity):
        #print(f"Activity {an_activity}")
        for an_agent in a_graph.objects(an_activity, PROV.wasAssociatedWith):
            #print(f"Activity {an_activity} associated with {an_agent}")
            for agent_label in a_graph.objects(an_agent, RDFS.label):
                #print(f"Agent label: {agent_label}")
                d_label = str(agent_label)
                pref_label = ""
                if d_label == "larch_athena":
                    pref_label = "process and normalise XAS"
                elif d_label == "larch_artemis":
                    pref_label = "FEFF fit of XAS"
                elif d_label == "larch_select_paths":
                    pref_label = "select FEFF paths"
                elif d_label == "larch_feff":
                    pref_label = "calculate FEFF paths from crystal"
                elif d_label == "larch_lcf":
                    pref_label = "linear combination fit of XAS"
                elif d_label == "larch_plot":
                    pref_label = "plot XAS data"
                elif d_label == "larch_criteria_report":
                    pref_label = "report on FEFF fitting"
                elif d_label == "DATA_FETCH":
                    pref_label = "fetch data from history"
                elif d_label == "EXTRACT_DATASET":
                    pref_label = "extract dataset from collection"
                    
            if pref_label != "":
                a_graph.add((an_activity, SKOS.prefLabel, Literal(pref_label)))

def cdif_activities(a_graph):
    for an_activity in a_graph.subjects(RDF.type, PROV.Activity):
        #print(f"Activity {an_activity}")
        for an_agent in a_graph.objects(an_activity, PROV.wasAssociatedWith):
            #print(f"Activity {an_activity} associated with {an_agent}")
            for agent_label in a_graph.objects(an_agent, RDFS.label):
                #print(f"Agent label: {agent_label}")
                d_label = str(agent_label)
                cdif_type = CDIFPROV.Analysis
                if d_label == "larch_athena":
                    cdif_type = CDIFPROV.Analysis
                elif d_label == "larch_artemis":
                    cdif_type = CDIFPROV.Analysis
                elif d_label == "larch_select_paths":
                    cdif_type = CDIFPROV.Deriving
                elif d_label == "larch_feff":
                    cdif_type = CDIFPROV.Deriving
                elif d_label == "larch_lcf":
                    cdif_type = CDIFPROV.Analysis
                elif d_label == "larch_plot":
                    cdif_type = CDIFPROV.Deriving
                elif d_label == "larch_criteria_report":
                    cdif_type = CDIFPROV.Deriving
                elif d_label == "DATA_FETCH":
                    cdif_type = CDIFPROV.DataProvisioning
                elif d_label == "EXTRACT_DATASET":
                    cdif_type = CDIFPROV.Extracting
                a_graph.add((an_activity, RDF.type, cdif_type))

# get label associated to a subject
def get_a_label(graph_thing, a_subject):
    # Try SKOS prefLabel
    for a_label in graph_thing.objects(a_subject, SKOS.prefLabel):
        return str(a_label)

    # Try RDFS label
    for a_label in graph_thing.objects(a_subject, RDFS.label):
        return str(a_label)

    return ""

# lookup the collections table to find the jobs associated to steps
def find_jobs_by_hda_id(invoked_jobs, data_collections, hda_list):
    jobs_for_step = []
    # Build lookup maps 
    # lookup map for jobs by hda_id
    jobs_by_output_hda = {
          list(job['output_dataset_mapping'].values())[0][0]: job for job in invoked_jobs
        }
    # lookup map for collections by collection id
    collections_by_id = {c['encoded_id']: c for c in data_collections}
    
    for hda_id in hda_list:
        collection = collections_by_id.get(hda_id)
        if not collection:
            continue
    
        for element in collection['collection']['elements']:
            element_hda_id = element['hda']['encoded_id']
    
            job = jobs_by_output_hda.get(element_hda_id)
            if job:
                #print(f"Found job {job['encoded_id']} for HDA {element_hda_id}")
                jobs_for_step.append(job['encoded_id'])
    #print (f"step id: {step_id}, jobs: {jobs_for_step}")
    return jobs_for_step

# lookup output dataset ids to get jobs associated to steps
def find_jobs_by_ds_ids(invoked_jobs, ds_ids_list):
    jobs_for_step = []
    # Build lookup maps 
    # lookup map for jobs by hda_id
    jobs_by_output_hda = {
          list(job['output_dataset_mapping'].values())[0][0]: job for job in invoked_jobs
        }    
    for ds_id in ds_ids_list:   
            job = jobs_by_output_hda.get(ds_id)
            if job:
                jobs_for_step.append(job['encoded_id'])
    return jobs_for_step

# job ids can be directly obtained from a job association, 
# implicit collection jobs or indirectly from
# dataset links or history dataset associations
# pending: generate activities and agents 
# for fetching scalar values (parameters)
def map_jobs_to_step(inv_step, invoked_jobs, ds_collections, ds_attributes, implicit_job_lookup):
    
    if inv_step.get("job"):
        return [inv_step["job"]["encoded_id"]]

    if inv_step.get("implicit_collection_jobs"):
        coll_id = inv_step["implicit_collection_jobs"].get("encoded_id")
        return implicit_job_lookup.get(coll_id, [])

    ds_links = [
        out["dataset_collection"]["encoded_id"]
        for out in inv_step.get("output_collections", [])
    ]
    
    job_ids = []
    if ds_links:
        job_ids += find_jobs_by_hda_id(invoked_jobs, ds_collections, ds_links)

    simple_outputs = [
        out["dataset"]["encoded_id"]
        for out in inv_step.get("outputs", [])
    ]
    ds_links += simple_outputs

    if simple_outputs:
        job_ids += find_jobs_by_ds_ids(invoked_jobs, simple_outputs)

        if not job_ids:
            copied_ids = [
                ds["copied_from_history_dataset_association_id_chain"][0]
                for ds in ds_attributes
                if ds["encoded_id"] in ds_links
            ]
            job_ids += find_jobs_by_ds_ids(invoked_jobs, copied_ids)
            
    return job_ids
    
# extract steps from wf and invocation files to create prov plan
def roc_provo(crate_path, out_path, output_file="galaxy_run_prov.ttl"):
    workflow_file = ""
    invocation_file = "" 

    # Load workflow (prospective provenance)
    wf = get_workflow_json(crate_path)
    steps = wf.get("steps", {})

    # Load invocation (retrospective provenance)
    inv = get_roc_json_part(crate_path,"invocation_attrs.txt")
    inv_steps = inv[0].get("steps", {})

    # load implicit job collections ()
    # these are parallelised executions from a single step in the workflow
    implicit_job_links = get_roc_json_part(crate_path, "implicit_collection_jobs_attrs.txt")
    
    implicit_job_lookup = {
        jc["encoded_id"]: jc["jobs"]
        for jc in implicit_job_links
    }
    
    # Load dataset attributes (encoding, names, ) 
    # to gather dataset attributes
    ds_attributes = get_roc_json_part(crate_path,"datasets_attrs.txt")

    # load ds collections
    # these collections map to grouped inputs (using lists) which are unpacked by fetch data
    ds_collections = get_roc_json_part(crate_path, "collections_attrs.txt")

    # Load job attributes
    # gather input links
    invoked_jobs = get_roc_json_part(crate_path,"jobs_attrs.txt")
    
    g = Graph()

    # define namespaces in graph
    for p, ns in [("prov", PROV), ("schema", SCHEMA), ("skos", SKOS), ("p-plan", PPLAN), 
                  ("cdifprov", CDIFPROV), ("cdif4xas", CDIF4XAS), ("panet", PANET),
                  ("sostdp", SOSTDP), ("ex", EX)]:
        g.bind(p, ns)

    base = "/"

    # --- 1. Workflow definition as prov:Plan ---
    wf_uri = URIRef(base + "workflow")
    g.add((wf_uri, RDF.type, PPLAN.Plan))
    g.add((wf_uri, RDFS.label, Literal(wf.get("name", "Galaxy Workflow"))))

    # --- 2. Prospective provenance: workflow steps ---
    for step_id, step in steps.items():
        step_uri = URIRef(base + f"step/{step_id}")
        g.add((step_uri, RDF.type, PPLAN.Step))
        step_label = step.get("label") or step.get("tool_id")
        g.add((step_uri, RDFS.label, Literal(step_label)))

        # Link step to workflow plan
        g.add(( step_uri, PPLAN.isStepOfPlan, wf_uri))

        # Prospective inputs
        for inp in step.get("input_connections", {}).values():
            if isinstance(inp, dict) and "id" in inp:
                src = URIRef(base + f"step/{inp['id']}")
                g.add((step_uri, PPLAN.isPrecededBy, src))
    
    # --- 3. Retrospective provenance: actual execution --- 
    # invocations are only used to link actities to wf steps
    for inv_step in inv_steps:
        job_ids = map_jobs_to_step(inv_step, invoked_jobs, ds_collections, ds_attributes, implicit_job_lookup)

        step_uri = URIRef(base + f"step/{inv_step['order_index']}")
        
        if not job_ids:
            print(f"*** Not Linked: {step_uri} ***")
            print(inv_step)
            continue
    
        
        for job_id in job_ids:
            g.add((
                URIRef(base + f"run/{job_id}"),
                PPLAN.correspondsToStep,
                step_uri
            ))

    # Add datset attributes
    for a_ds in ds_attributes:
        ent_uri = (URIRef(base + f"dataset/{a_ds['encoded_id']}"))
        format_str =  file_formats[a_ds['extension']]

        g.add((ent_uri, RDF.type, PROV.Entity)) # duplicated only used for WF_inputs which are not in invocation
        g.add((ent_uri, RDF.type, CDIFPROV.Dataset)) #test adding cdif terminology
        g.add((ent_uri, DCTERMS.format, Literal(format_str)))
        g.add((ent_uri, DCTERMS.description, Literal(a_ds['info'])))
        g.add((ent_uri, SCHEMA.id, Literal(a_ds['file_name'])))
        g.add((ent_uri, SKOS.prefLabel, Literal(a_ds['name']) ))
        if a_ds['extension'] in data_products:
            g.add((ent_uri, RDF.type, CDIFPROV.DataProduct))
        # placeholder for external file describing the ds in detail:
        #g.add((ent_uri, SCHEMA.subjectOf, URIRef(f"{str(ent_uri)[1:].replace('/','_')}.jsonld")))
        g.add ((ent_uri, RDF.type, SCHEMA.MediaObject))

    # Add the missing links to inputs
    for a_job in invoked_jobs:
        job_uri = URIRef(base + f"run/{a_job['encoded_id']}")
        # link all used datasets to activites
        for a_mapping in a_job['input_dataset_mapping']:
            for a_ds_id in  a_job['input_dataset_mapping'][a_mapping]:
                ds_uri = URIRef(base + f"dataset/{a_ds_id}")
                g.add((job_uri, PROV.used, ds_uri))
                
    for a_job in invoked_jobs:
        job_uri = URIRef(base + f"run/{a_job['encoded_id']}")
        tool_label = a_job['tool_id'].lstrip("_").rstrip("_")
        tool_uri = URIRef(f"/srv/galaxy/var/shed_tools/{a_job['tool_id']}")# causing problems
        tool_version = a_job['tool_version']
        if "toolshed" in a_job['tool_id']:
            tool_label, tool_version  =   a_job['tool_id'].split("/")[-2:]
        elif a_job['command_line']:
             tool_uri = URIRef(str(a_job['command_line'].split(' ')[1].strip("'")))
        else:
            tool_uri = URIRef(base + f"galaxy_tool/{tool_label.lower()}")

        g.add((tool_uri, RDF.type, PROV.SoftwareAgent))
        g.add((tool_uri, RDF.type, CDIFPROV.Machine)) #test adding cdif terminology
        g.add((tool_uri, RDFS.label, Literal(tool_label)))
        g.add((tool_uri, SCHEMA.softwareVersion, Literal(tool_version)))
        # This should only add labes for datafetch activites which are not invocations
        g.add((job_uri, RDF.type, PROV.Activity))
        g.add((job_uri, RDFS.label, Literal(tool_label)))
        g.add((job_uri, PROV.wasAssociatedWith, tool_uri))
        
        # link output_dataset_mappings
        for a_mapping in a_job['output_dataset_mapping']:
            for a_mapping_id in  a_job['output_dataset_mapping'][a_mapping]:
                a_ds_id = get_history_mapped_ds(ds_attributes, a_mapping_id)
                ds_uri = URIRef(base + f"dataset/{a_ds_id}")
                g.add((ds_uri, PROV.wasGeneratedBy, job_uri)) #already done for most only pending for data fetch
                g.add((ds_uri, PROV.wasAttributedTo, tool_uri))
                
                # these are also for data fetch only
                # link to associated plan activity
                step_uri = get_wf_step(ds_uri, g)
                if step_uri != None:
                    g.add((job_uri, PPLAN.correspondsToStep, step_uri))
        
        for a_mapping in a_job['input_dataset_mapping']:
            for a_ds_id in  a_job['input_dataset_mapping'][a_mapping]:
                ds_uri = URIRef(base + f"dataset/{a_ds_id}")
                g.add((ds_uri, PROV.wasAttributedTo, tool_uri))
                
    # Assing human readable labels to activities
    custom_labels(g)

    # add cdif entity types
    cdif_activities(g)

    # --- Save ---
    save_ttl = Path(out_path, output_file)
    g.serialize(destination=save_ttl, format="turtle")
    
    graph_context={
            "prov": str(PROV),
            "p-plan": str(PPLAN),
            "schema": str(SCHEMA),
            "skos": str(SKOS),
            "rdfs": str(RDFS),
            "dcterms": str(DCTERMS),
            "cdifprov": str(CDIFPROV),
            "cdif4xas": str(CDIF4XAS)
        }
    save_json = Path(out_path, output_file[:-4]+".jsonld")
    g.serialize(destination=save_json, format="json-ld", publicID="local:",
                context=graph_context, auto_compact=True, indent=2)
    return g 

# These are the functions to draw the provenance graph
from rdflib import Graph, Namespace, RDF
from graphviz import Digraph
from IPython.display import display

import os

# this path is needed for grapviz to work on win
os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin/'

def draw_pplan_only(a_graph):
    dot = Digraph("prov")
    for s, p, o in a_graph:
        node_str = get_a_label(a_graph, s)
        if (s, RDF.type, PPLAN.Step) in a_graph:
            if not ("/run/") in str(s):
                node_str = str(s) # don convert steps, their label is the tool ID
            dot.node(s, label=node_str, shape="box")
        elif (s, RDF.type, PROV.Activity) in a_graph:
            if not ("/run/") in str(s):
                node_str = str(s) # don convert steps, their label is the tool ID
            dot.node(s, label = f"<f0>|<f1>{node_str}|<f2> ", shape="record", style="filled", fillcolor="#b2d8ff")
        if p.startswith(PPLAN):
            if "correspondsTo" in str(p):
                dot.edge(str(s), str(o), label=p.split("#")[-1], style="dashed")
            else:
                dot.edge(str(s), str(o), label=p.split("#")[-1])
    return dot

def draw_prov_only(a_graph):
    dot = Digraph("prov")

    for s, p, o in a_graph:
        # classify nodes
        node_str = get_a_label(a_graph, s)
        if node_str == "":
            node_str = str(s) 
        if (s, RDF.type, PROV.Entity) in a_graph:
            dot.node(s, label=node_str, shape="box", style="rounded, filled", fillcolor="#fff2b2")
        elif (s, RDF.type, PROV.Activity) in a_graph:
            if not ("/run/") in str(s):
                node_str = str(s) # don convert steps, their label is the tool ID
            dot.node(s, label = f"<f0> |<f1>{node_str}|<f2> ", shape="record", style="filled", fillcolor="#b2d8ff")
        elif (s, RDF.type, PROV.SoftwareAgent) in a_graph:
            dot.node(s, label=node_str, shape="house", style="filled", fillcolor="#c2f0c2")            
    
        # add edges with labels
        if p.startswith(PROV):
            dot.edge(str(s), str(o), label=p.split("#")[-1])
    return dot

def draw_prov_full(a_graph):
    dot = Digraph("prov")

    for s, p, o in a_graph:
         # classify nodes
        node_str = get_a_label(a_graph, s)
        if node_str == "":
            node_str = str(s) 
        if (s, RDF.type, PROV.Entity) in a_graph:
            dot.node(s, label=node_str, shape="box", style="rounded, filled", fillcolor="#fff2b2")
        elif (s, RDF.type, PROV.Activity) in a_graph:
            if not ("/run/") in str(s):
                node_str = str(s) # don convert steps, their label is the tool ID
            dot.node(s, label = f"<f0>|<f1>{node_str}|<f2> ", shape="record", style="filled", fillcolor="#b2d8ff")
        elif (s, RDF.type, PROV.SoftwareAgent) in a_graph:
            dot.node(s, label=node_str, shape="house", style="filled", fillcolor="#c2f0c2")
        elif (s, RDF.type, PPLAN.Step) in a_graph:
            if not ("/run/") in str(s):
                node_str = str(s) # don convert steps, their label is the tool ID
            dot.node(s, label=node_str, shape="box")
            
    
        # add edges with labels
        if p.startswith(PROV):
            dot.edge(str(s), str(o), label=p.split("#")[-1])
        elif p.startswith(PPLAN):
            if "correspondsTo" in str(p):
                dot.edge(str(s), str(o), label=p.split("#")[-1], style="dashed")
            else:
                dot.edge(str(s), str(o), label=p.split("#")[-1])
    return dot

# get a dataframe with the details of the datasets
# put provenance in a table structure
import pandas as pd
# present data as html table
from IPython.display import display, HTML

def get_datasets_prov(roc_graph):
    qres = roc_graph.query("""
    PREFIX prov:   <http://www.w3.org/ns/prov#>
    PREFIX skos:   <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX schema:<https://schema.org/>
    PREFIX pplan: <https://vocab.linkeddata.es/p-plan#>
    
    SELECT
      ?step
      ?dataset
      ?activityLabel
      ?tools
      ?inputs
    WHERE {
      # --------------------------------------------------
      # core relation
      # --------------------------------------------------
      ?output prov:wasGeneratedBy ?activity .
    
      # --------------------------------------------------
      # output (dataset) label — ONE label per output
      # --------------------------------------------------
      OPTIONAL {
        SELECT ?output
               (COALESCE(MAX(?pref), MAX(?name), MAX(?label), STR(?output)) AS ?dataset)
        WHERE {
          OPTIONAL { ?output skos:prefLabel ?pref }
          OPTIONAL { ?output schema:name    ?name }
          OPTIONAL { ?output rdfs:label     ?label }
        }
        GROUP BY ?output
      } 
    
      # --------------------------------------------------
      # wf step — related to activity
      # --------------------------------------------------
      OPTIONAL {
        SELECT ?activity
               ?step
        WHERE {
          ?activity pplan:correspondsToStep ?step .
        }
      }
    
      # --------------------------------------------------
      # activity label — ONE label per activity
      # --------------------------------------------------
      OPTIONAL {
        SELECT ?activity
               (COALESCE(MAX(?pref), MAX(?name), MAX(?label), STR(?activity)) AS ?activityLabel)
        WHERE {
          OPTIONAL { ?activity skos:prefLabel ?pref }
          OPTIONAL { ?activity schema:name    ?name }
          OPTIONAL { ?activity rdfs:label     ?label }
        }
        GROUP BY ?activity
      }
    
      # --------------------------------------------------
      # tools / agents — MANY tools aggregated per activity
      # --------------------------------------------------
      OPTIONAL {
        SELECT ?activity
               (GROUP_CONCAT(DISTINCT COALESCE(?pref, ?name, ?label, STR(?tool)); separator=", ") AS ?tools)
        WHERE {
          ?activity prov:wasAssociatedWith ?tool .
          OPTIONAL { ?tool skos:prefLabel ?pref }
          OPTIONAL { ?tool schema:name    ?name }
          OPTIONAL { ?tool rdfs:label     ?label }
        }
        GROUP BY ?activity
      }
    
      # --------------------------------------------------
      # inputs — MANY inputs aggregated per activity
      # --------------------------------------------------
      OPTIONAL {
        SELECT ?activity
               (GROUP_CONCAT(DISTINCT COALESCE(?pref, ?name, ?label, STR(?input)); separator=", ") AS ?inputs)
        WHERE {
          ?activity prov:used ?input .
          OPTIONAL { ?input skos:prefLabel ?pref }
          OPTIONAL { ?input schema:name    ?name }
          OPTIONAL { ?input rdfs:label     ?label }
        }
        GROUP BY ?activity
      }
    }
    ORDER BY ?step
    """)
    
    df = pd.DataFrame(
        [(str(s), str(a), str(t), str(o), str(i)) for s, o, a, t, i in qres],
        columns=["Step", "Activity", "Tool", "Dataset", "Inputs"]
    )
    return df

# Show dataset details

# get a dict of dataset details
def get_dataset_properties(a_dataset, a_graph):
    ds_data = []
    relations = list(a_graph.predicate_objects(a_dataset))
    ds_data = [[p, o] for p, o in relations]
    return ds_data

def get_ds_dataframe(ds_details, a_graph):
    processed_properties = []
    for p, o in ds_details:
        short_p = a_graph.namespace_manager.normalizeUri(p)
        short_o = a_graph.namespace_manager.normalizeUri(o) if isinstance(o, URIRef) else o
        if "prov:wasAttributedTo" == str(short_p) or \
           "prov:wasGeneratedBy" == str(short_p):
            short_o = get_a_label(a_graph, o)
        processed_properties.append([short_p, short_o])
    ds_df = pd.DataFrame(
        [(p,o) for p, o in processed_properties],
        columns=["Property", "Value"]
    )
    return ds_df

def add_panet(ds_details, *terms):
    seen = {o for p, o in ds_details if p == DCTERMS.subject}
    
    for term in terms:
        panet_uri = PANET_IDS[term]
        if panet_uri not in seen:
            ds_details.append((DCTERMS.subject, panet_uri))

def extract_context(ds_id, graph):
    formats = {str(o) for o in graph.objects(ds_id, DCTERMS.format)}
    generated_by = [
        get_a_label(graph, o)
        for o in graph.objects(ds_id, PROV.wasGeneratedBy)]

    used_by = [
        get_a_label(graph, s)
        for s in graph.subjects(PROV.used, ds_id)]

    return {
        "formats": formats,
        "generated_by": " ".join(generated_by).lower(),
        "used_by": " ".join(used_by).lower()}
    
def add_panet_class(ds_id, ds_details, a_graph):
    context = extract_context(ds_id, a_graph)
    #print (context)
    for rule in PANET_RULES:
        if rule["when"](context):
            add_panet(ds_details, *rule["add"])
    return ds_details

def add_sweet_pl(ds_details, *terms):
    seen = {o for p, o in ds_details if p == DCTERMS.subject}
    for term in terms:
        swpl_uri = PROCESSING_LEVELS[term]
        if swpl_uri not in seen:
            ds_details.append((DCTERMS.subject, swpl_uri))

def add_processing_level(ds_id, ds_details, a_graph):
    context = extract_context(ds_id, a_graph)
    for rule in SOSTDP_RULES:
        if rule["when"](context):
            add_sweet_pl(ds_details, *rule["add"])
    return ds_details

def get_ancestry(ds_id, graph):    
    generated_by = [o for o in graph.objects(ds_id, PROV.wasGeneratedBy)]
    for an_action in generated_by:
        inputs = [s for s in graph.objects(an_action, PROV.used)]
    return {"generated_by": generated_by,
        "inputs": inputs}

def add_ancestor(ds_id, ds_details, a_graph):
    ancestry = get_ancestry(ds_id, a_graph)
    #print ("Ancestry: ", ancestry)
    #print ("Just inputs:", ancestry["inputs"])
    for an_input in ancestry["inputs"]:
        #a_graph.add((ds_id, PROV.wasDerivedFrom, an_input))
        ds_details.append([PROV.wasDerivedFrom, an_input])
    #        add_panet(ds_details, *rule["add"])
    return ds_details
    
PANET_RULES = [
    # CIF or input => crystallography OK
    {
        "when": lambda c: "chemical/x-cif" in c["formats"],
        "add": ["Crystallography"],
    },
    
    # any generated by feff path crystallography OK
    {
        "when": lambda c: "feff path" in c["generated_by"],
        "add": ["Crystallography"],
    },
    
    # Data fetch and fed to normalise xas => XAS
    # project, txt, 'any' fed to normalise xas 
    {
        "when": lambda c: "fetch data" in c["generated_by"]
                          and "normalise xas" in c["used_by"],
        "add": ["XAS"],
    },

    # any generated by normalise xas OK
    {
        "when": lambda c: "normalise xas" in c["generated_by"],
        "add": ["XANES"],
    },

    # any from Artemis => XAFS + EXAFS
    {
        "when": lambda c: "feff fit" in c["generated_by"],
        "add": ["EXAFS"],
    },

    # Plot after Athena → XANES
    {
        "when": lambda c: "normalise xas" in c["generated_by"]
                          and "plot" in c["used_by"],
        "add": ["XANES"],
    },
]

SOSTDP_RULES = [
    # CIF or input => derived data level 3
    {
        "when": lambda c: "chemical/x-cif" in c["formats"],
        "add": ["derived"],
    },
    
    # any generated by feff path crystallography OK
    {
        "when": lambda c: "feff path" in c["generated_by"],
        "add": ["derived"],
    },
    
    # Data fetch and fed to normalise level 0
    # nexus, txt, 'any' fed to normalise xas 
    {
        "when": lambda c: "fetch data" in c["generated_by"]
                          and "normalise xas" in c["used_by"]
                          and ("text/plain" in c["formats"] 
                               or "application/nexus" in c["formats"]),
        "add": ["raw"],
    },

    # any prj is processed
    {
        "when": lambda c: "application/vnd.demeter.athena" in c["formats"],
        "add": ["processed"],
    },
    
    # any plot is a product
    {
        "when": lambda c: "image/png" in c["formats"],
        "add": ["product"],
    },

    # text from Artemis => current only generates report no spectra
    {
        "when": lambda c: "feff fit" in c["generated_by"]
                      and "text/plain" in c["formats"], 
        "add": ["derived"],
    },

    # any from Artemis => if we get nexus or xdi
    {
        "when": lambda c: "feff fit" in c["generated_by"]
                      and ("application/nexus" in c["formats"]
                          or "application/xdi"  in c["formats"]),
        "add": ["transformed"],
    },
                          
    # text after LCF => current only generates report no spectra
    {
        "when": lambda c: "lcf fit" in c["generated_by"]
                          and "text/plain" in c["used_by"],
        "add": ["derived"],
    },
    
    # any after LCF => if we get nexus or xdi
    {
        "when": lambda c: "lcf fit" in c["generated_by"]
                          and ("application/nexus" in c["formats"]
                          or "application/xdi"  in c["formats"]),
        "add": ["derived"],
    },
]


def get_ancestors(graph, entity):
    seen = set()
    stack = [entity]
    while stack:
        current = stack.pop()
        for activity in graph.objects(current, PROV.wasGeneratedBy):
            for parent in graph.objects(activity, PROV.used):
                if parent not in seen:
                    seen.add(parent)
                    stack.append(parent)
    return seen

def get_descendants(graph, entity):
    seen = set()
    stack = [entity]
    while stack:
        current = stack.pop()
        for activity in graph.subjects(PROV.used, current):
            for child in graph.subjects(
                PROV.wasGeneratedBy,
                activity
            ):
                if child not in seen:
                    seen.add(child)
                    stack.append(child)
    return seen

def get_full_ancestry(a_graph, an_entity):
    all_ancestors = get_ancestors(a_graph, an_entity)
    all_descendants = get_descendants(a_graph, an_entity)
    return {"entity": an_entity, "ancestors": all_ancestors, "descendants": all_descendants}

def get_values_custom_xmu_textfile(file_path, filename):
    f = get_file_from_rocratezip(file_path, filename)
    return_dict = {}
    for line in f:
        text = line.decode('utf-8')
        if text[0] == "#":
            if "#%name:" in text: 
                #print(f"name: {text[7:].strip()}")
                return_dict["sample_name"] = text[7:].strip()
            elif "#%atom:" in text: 
                #print(f"Sample: {text[7:].strip()}")
                return_dict["sample_formula"] = text[7:].strip()
            elif "#%edge:" in str(line): 
                #print(f"Edge: {text[7:].strip()}")
                return_dict["edge"] = text[7:].strip()
            elif "#%temp:" in str(line): 
                #print(f"Temperature: {text[7:].strip()}")
                return_dict["temperature"] = text[7:].strip()
            elif "#%beam:" in str(line): 
                #print(f"Beamline: {text[7:].strip()}")
                return_dict["beamline"] = text[7:].strip()
        else:
          break
    return return_dict

def get_values_custom_dat_textfile(file_path, filename):
    f = get_file_from_rocratezip(file_path, filename)
    return_dict = {}
    for line in f:
        text = line.decode('utf-8')
        if text[0] == "#":
            if "# Sample name:" in text: 
                return_dict["sample_name"] = text.replace("# Sample name:", "").strip()
            elif "#%atom:" in text: 
                #print(f"Sample: {text[7:].strip()}")
                return_dict["sample_formula"] = text[7:].strip()
            elif "#%edge:" in str(line): 
                #print(f"Edge: {text[7:].strip()}")
                return_dict["edge"] = text[7:].strip()
            elif "#%temp:" in str(line): 
                #print(f"Temperature: {text[7:].strip()}")
                return_dict["temperature"] = text[7:].strip()
            elif "# Instrument:" in str(line): 
                return_dict["beamline"] = text.replace("# Instrument:", "").strip()
        else:
          break
    return return_dict

def get_entity_type(graph_thing, an_entity):
    for a_type in graph_thing.objects(an_entity, DCTERMS.format):
        return a_type

def get_entity_path(graph_thing, an_entity):
    for a_path in graph_thing.objects(an_entity, SCHEMA.id):
        return a_path

def get_entity_description(graph_thing, an_entity):
    for a_desc in graph_thing.objects(an_entity, DCTERMS.description):
        return a_desc

def get_entity_metadata(roc_path, graph_thing, an_entity):
    a_type = str(get_entity_type(graph_thing, an_entity))
    
    vals_entity = {}
    
    # text types
    if a_type in ["text/plain", "chemical/x-cif", 
                  "text/csv", "application/xdi"]:
        filename = str(get_entity_path(graph_thing, an_entity))
        if get_a_label(graph_thing, an_entity)[-4:] == ".xmu":
            vals_entity = get_values_custom_xmu_textfile(roc_path, filename)
        elif get_a_label(graph_thing, an_entity)[-4:] == ".dat":
            vals_entity = get_values_custom_dat_textfile(roc_path, filename)
        # need other methods for xdi and other text files from different beamlines
    elif a_type in ["application/vnd.demeter.athena"]:
        # athena project files
        entity_desc = get_entity_description(graph_thing, an_entity)
        vals_entity = get_values_athena_project(entity_desc)
    return vals_entity

def get_values_athena_project(athena_descr):
    athena_split = athena_descr.split("\n")
    return_dict = {}
    for a_line in athena_split:
        [k,v] = a_line.split(": ")
        if k == "atsym":
             k =  "element"
        elif k == 'bkg_e0':
            k = "e0"
        elif k == 'npts':
            k = "points"
        elif k == 'xmax':
            k = 'energy_max'
        elif k == 'xmin':
            k = 'energy_min'
        return_dict[k] = v 
    return return_dict

def add_cdif_metadata(an_entity, ds_properties, roc_graph, a_file_path):
    
    #print (get_a_label(roc_graph, an_entity), '->')
    entity_ancestry = get_full_ancestry(roc_graph, an_entity)
    branch_metadata = {}
    branch_metadata[entity_ancestry["entity"]] = get_entity_metadata(a_file_path, roc_graph, entity_ancestry["entity"])
    
    for an_ancestor in entity_ancestry["ancestors"]:
        branch_metadata[an_ancestor] = get_entity_metadata(a_file_path, roc_graph, an_ancestor)
    
    for a_descendant in entity_ancestry["descendants"]:
        branch_metadata[a_descendant] = get_entity_metadata(a_file_path, roc_graph, a_descendant)
    
    # for the first case is OK to join them all
    
    sinlge_metadata = {}
    
    for an_entity in branch_metadata:
        if branch_metadata[an_entity] != {}:
            sinlge_metadata = sinlge_metadata|branch_metadata[an_entity]
    
    # actual metadata pairs
    branch_prov_metadata = [] 
    for a_key in sinlge_metadata:
            if a_key in ["element", "e0", "edge", "sample_name", 
                         "sample_formula", "beamline"]:
                pred = CDIF4XAS[a_key]
                branch_prov_metadata.append([pred, Literal(sinlge_metadata[a_key])])
    
    ds_properties += branch_prov_metadata
    return ds_properties

def show_datasets(roc_graph, roc_path, output_path="", show_only = False):
    step_datasets_qry = """
    PREFIX prov:  <http://www.w3.org/ns/prov#>
    PREFIX pplan: <https://vocab.linkeddata.es/p-plan#>
    
    SELECT
      ?step
      ?dataset
      ?activity
    WHERE {
      ?dataset prov:wasGeneratedBy ?activity .
      OPTIONAL {
        ?activity pplan:correspondsToStep ?step .
      }
    }
    ORDER BY ?step
    """
    qres = roc_graph.query(step_datasets_qry)
    
    ds_jsons=[]
    
    for step, a_ds, activity,  in qres:
        graph_context={
            "prov": str(PROV),
            "schema": str(SCHEMA),
            "skos": str(SKOS),
            "rdfs": str(RDFS),
            "dcterms": str(DCTERMS),
            "panet": str(PANET),
            "cdifprov": str(CDIFPROV),
            "cdif4xas": str(CDIF4XAS),
            "sostdp": str(SOSTDP),
            "ex": str(EX)
        }
        
        new_graph = Graph()
        for p, ns in [("prov", PROV), ("schema", SCHEMA), ("skos", SKOS), ("p-plan", PPLAN), 
                      ("cdifprov", CDIFPROV), ("cdif4xas", CDIF4XAS), ("panet", PANET), 
                      ("sostdp", SOSTDP), ("ex", EX) ]:
            new_graph.bind(p, ns)
        
        #print(str(step), str(dataset), str(activity))
        ds_properties = get_dataset_properties(a_ds,roc_graph)
        ds_properties = add_panet_class(a_ds, ds_properties, roc_graph)
        ds_properties = add_processing_level(a_ds, ds_properties, roc_graph)
        ds_properties = add_ancestor(a_ds, ds_properties, roc_graph)
        ds_properties = add_cdif_metadata(a_ds, ds_properties, roc_graph, roc_path)
        ds_label = get_a_label(roc_graph, a_ds)
        props_df = get_ds_dataframe(ds_properties, roc_graph)
        display(HTML(f"<h3>{ds_label} Properties ({a_ds})</h3>") )
        display(HTML(props_df.to_html().replace("\\n","<br>")))
    
        json_file = f"{str(a_ds)[1:].replace('/','_')}.jsonld"
        save_json = Path(output_path, json_file)
        
        ds_jsons.append(json_file)
        
        subj_id = URIRef(json_file)
    
        for p, o in ds_properties:
            #if not "prov" in str(p) :
            new_graph.add((subj_id,p,o))
        #actual_context = extract_namespaces(new_graph)
        new_graph.add((subj_id, SCHEMA.about, a_ds) )
        # highlight as a creativework?
        new_graph.add((subj_id, RDF.type, SCHEMA.CreativeWork) )

        if not show_only:
            new_graph.serialize(destination=save_json, format="json-ld", 
                    context= graph_context, auto_compact=True, indent=2)
    
    return ds_jsons
