import os
import pymupdf
import definitions
import glob
from typing_extensions import TypedDict
from typing import Annotated, Any, Union, List, Dict
from langgraph.graph.message import MessagesState
from src import utils

def merge_update(current_value, new_value):
    """
    Reducer function that merges updates from parallel branches.
    It prefers the new_value, unless the new_value is None, in which case it keeps the current_value.
    This prevents valid data from being overwritten by None from other branches.
    """
    if new_value is not None:
        return new_value
    return current_value


class State(MessagesState):
    # --- Internal Fields for Graph Logic ---
    path:       Annotated[Union[str, None], merge_update]
    raw_text:   Annotated[Union[str, None], merge_update]
    landmarks:  Annotated[Union[Dict, None], merge_update]
    ocr_needed: Annotated[Union[bool, None], merge_update]
    relevancy:  Annotated[Union[bool, None], merge_update]

    # --- Core Metadata ---
    title:                  Annotated[Union[str, None], merge_update]
    authors:                Annotated[Union[List[str], None], merge_update]
    author_affiliations:    Annotated[Union[List[str], None], merge_update]
    year:                   Annotated[Union[int, None], merge_update]
    publication_date:       Annotated[Union[str, None], merge_update]
    journal:                Annotated[Union[str, None], merge_update]
    publisher:              Annotated[Union[str, None], merge_update]
    doi:                    Annotated[Union[str, None], merge_update]
    keywords:               Annotated[Union[List[str], None], merge_update]
    abstract:               Annotated[Union[str, None], merge_update]

    # --- Core Research Content ---
    problem_statement:      Annotated[Union[str, None], merge_update]
    proposed_model_name:    Annotated[Union[str, None], merge_update]
    methodology:            Annotated[Union[str, None], merge_update]
    experimental_methods:   Annotated[Union[List[str], None], merge_update]
    main_findings:          Annotated[Union[str, None], merge_update]

    # --- Critical Analysis ---
    usp:            Annotated[Union[str, None], merge_update]
    limitations:    Annotated[Union[str, None], merge_update]
    future_work:    Annotated[Union[str, None], merge_update]

    # --- Data Fields ---
    dataset_name:       Annotated[Union[str, None], merge_update]
    source_type:        Annotated[Union[str, None], merge_update]
    granularity_scale:  Annotated[Union[str, None], merge_update]
    dataset_duration:   Annotated[Union[str, None], merge_update]
    resolution:         Annotated[Union[str, None], merge_update]
    num_data_points:    Annotated[Union[str, None], merge_update]
    data_description:   Annotated[Union[str, None], merge_update]

    # --- Experimental Setup ---
    train_test_split:   Annotated[Union[str, None], merge_update]
    horizon:            Annotated[Union[str, None], merge_update]
    features_used:      Annotated[Union[List[str], None], merge_update]
    data_preprocessing: Annotated[Union[List[str], None], merge_update]
    metrics:            Annotated[Union[List, None], merge_update]

    # --- Reproducibility ---
    data_availability:  Annotated[Union[str, None], merge_update]
    code_availability:  Annotated[Union[str, None], merge_update]


def initialise_state() -> State:
    return {"messages": ['Paper Analysis'],

            "landmarks":            None,
            "raw_text":             None,
            "ocr_needed":           None,

            # Core Metadata
            "path":                 None,
            "title":                None,
            "authors":              None,
            "author_affiliations":  None,
            "year":                 None,
            "publication_date":     None,
            "journal":              None,
            "publisher":            None,
            "doi":                  None,
            "keywords":             None,
            "abstract":             None,

            # Core Research Content
            "problem_statement":    None,
            "proposed_model_name":  None,
            "methodology":          None,
            "main_findings":        None,
            "experimental_methods": None,

            # Critical Analysis
            "usp":                  None,
            "limitations":          None,
            "future_work":          None,

            # Data Fields
            "dataset_name":         None,
            "source_type":          None,
            "granularity_scale":    None,
            "dataset_duration":     None,
            "resolution":           None,
            "num_data_points":      None,
            "data_description":     None,

            # Experimental Setup
            "train_test_split":     None,
            "horizon":              None,
            "features_used":        None,
            "data_preprocessing":   None,
            "metrics":              None,

            # Reproducibility
            "data_availability":    None,
            "code_availability":    None,

            # Internal Meta-Field
            "relevancy":            None}


def read_paper():

    path = definitions.paper_path

    paper_list = glob.glob(str(path) + "/*.pdf")
    print(paper_list)

    master_data = {}
    for paper_name in paper_list:
        data = initialise_state()
        paper = pymupdf.open(paper_name)
        # print(paper.metadata)

        file_name = str.split(str.split(paper_name, "\\")[1], ".")[0]

        data['path'] = paper_name

        if 'title' in paper.metadata:
            title = paper.metadata['title']
            data['title'] = title

        if 'creator' in paper.metadata:
            creator = paper.metadata['creator']
            data['publisher'] = creator

        if 'keywords' in paper.metadata:
            keywords = paper.metadata['keywords']
            keywords = keywords.split(',')
            data['keywords'] = keywords

        master_data[file_name] = data

    return master_data
