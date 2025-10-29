from langgraph.graph import StateGraph, END, START
from src.initialise_state import State
from src import nodes
from dotenv import load_dotenv
load_dotenv()

def route_for_metadata_quality(state: State) -> str:
    """If key landmarks are missing after the first pass, route to OCR."""
    landmarks = state.get('landmarks', {})
    if state.get('ocr_needed') is True:
        return "extract_metadata" # Already tried OCR, give up and extract what we can
    if landmarks.get('abstract_start', -1) == -1 and landmarks.get('introduction_start', -1) == -1:
        return "perform_ocr"
    return "extract_metadata"


def route_by_relevancy(state: State) -> str:
    """
    Reads the 'relevancy' boolean from the state and returns the corresponding
    string path for the conditional edge.
    """
    if state.get('relevancy') is True:
        return "relevant"
    else:
        return "not_relevant"


def create_graph():
    """Builds and compiles the complete LangGraph pipeline."""
    builder = StateGraph(State)

    # --- Add all nodes from nodes.py ---
    builder.add_node("direct_metadata_extract", nodes.extract_from_pdf_metadata)
    builder.add_node("read_and_locate_landmarks", nodes.read_and_locate_landmarks)
    builder.add_node("perform_ocr", nodes.ocr_and_relocate_landmarks)
    builder.add_node("extract_metadata", nodes.extract_sliced_metadata)

    # --- Use the new relevancy node ---
    builder.add_node("check_relevancy", nodes.check_paper_relevancy)

    # The relevant/not_relevant nodes are just for setting the final state flag
    builder.add_node("not_relevant", nodes.not_relevant_node)
    builder.add_node("relevant", nodes.relevant_node)

    # Analysis nodes
    builder.add_node("extract_methodology", nodes.extract_methodology_and_models)
    builder.add_node("extract_analysis", nodes.extract_analysis_and_findings)
    builder.add_node("extract_dataset", nodes.extract_dataset_properties)
    builder.add_node("extract_experiments", nodes.extract_experimental_setup)
    builder.add_node("join_branches", nodes.dummy_node)

    # --- Define the graph's edges ---
    builder.add_edge(START, "direct_metadata_extract")
    builder.add_edge("direct_metadata_extract", "read_and_locate_landmarks")
    builder.add_conditional_edges("read_and_locate_landmarks", route_for_metadata_quality, {
        "perform_ocr": "perform_ocr",
        "extract_metadata": "extract_metadata"
    })
    builder.add_edge("perform_ocr", "extract_metadata")

    # After metadata, run the relevancy check
    builder.add_edge("extract_metadata", "check_relevancy")

    # --- Use the new conditional router ---
    builder.add_conditional_edges(
        "check_relevancy",  # The edge starts AFTER the check is done
        route_by_relevancy,  # The router function decides the path
        {
            "relevant": "relevant",
            "not_relevant": "not_relevant"
        }
    )

    # The "not_relevant" path now goes to its simple node and then ends
    builder.add_edge("not_relevant", END)

    # Parallel fork for relevant papers
    builder.add_edge("relevant", "extract_methodology")
    builder.add_edge("relevant", "extract_analysis")
    builder.add_edge("relevant", "extract_dataset")
    builder.add_edge("relevant", "extract_experiments")

    # Join parallel branches
    builder.add_edge("extract_methodology", "join_branches")
    builder.add_edge("extract_analysis", "join_branches")
    builder.add_edge("extract_dataset", "join_branches")
    builder.add_edge("extract_experiments", "join_branches")

    builder.add_edge("join_branches", END)

    # builder.add_edge("extract_metadata", END)
    return builder.compile()