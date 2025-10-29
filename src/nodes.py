import json
import re
import pymupdf
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from src.initialise_state import State
from src import utils
from dotenv import load_dotenv
load_dotenv()

from src.prompts.water_demand_forecasting import prompts
# from src.prompts.power_system_protection import prompts

# --- Initialize the Gemini client here, so all nodes can share it ---
api_key = os.environ.get("GOOGLE_API_KEY")
gemini = ChatGoogleGenerativeAI(model='gemini-2.5-pro', temperature=0.0, google_api_key=api_key)

# --- INGESTION & METADATA NODES ---
def _locate_landmarks_with_re(text: str) -> dict:
    """A helper function to find landmarks using regular expressions."""
    # Define all the patterns in one place for easy management.
    # We include common variations.
    landmark_patterns = {
        "abstract_start": re.compile(r'A\s*B\s*S\s*T\s*R\s*A\s*C\s*T|ABSTRACT', re.IGNORECASE),
        "keywords_start": re.compile(r'Keywords|Key words|Index Terms', re.IGNORECASE),
        "introduction_start": re.compile(r'1\.\sIntroduction|Introduction', re.IGNORECASE),
        "references_start": re.compile(r'References|Bibliography', re.IGNORECASE),
        "page_end": re.compile(r'--- Page Break ---', re.IGNORECASE)

    }

    landmarks = {}
    for name, pattern in landmark_patterns.items():
        match = pattern.search(text)
        # If a match is found, store its starting index. Otherwise, store -1.
        landmarks[name] = match.start() if match else -1

    return landmarks


def read_and_locate_landmarks(state: State) -> State:
    print("--- NODE: Reading PDF & Locating Landmarks (RE-based) ---")
    try:
        paper = pymupdf.open(state['path'])
        text = utils.extract_text_from_all_pages(paper)
        paper.close()
        state['raw_text'] = text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        state['raw_text'] = ""

    # Use the deterministic helper function instead of an LLM call
    state['landmarks'] = _locate_landmarks_with_re(state.get('raw_text', ''))

    print(f"Landmarks found: {state['landmarks']}")
    return state


def ocr_and_relocate_landmarks(state: State) -> State:
    print("--- NODE: Performing OCR & Relocating Landmarks (RE-based) ---")
    state['ocr_needed'] = True
    paper = pymupdf.open(state['path'])
    page_one = paper.load_page(0)
    ocr_text = utils.ocr_page_text(page_one)
    paper.close()

    # The logic to combine standard and OCR text remains useful.
    raw_text = state.get('raw_text', '')
    if ocr_text.strip():  # Only add if OCR returned something
        # A simple way to avoid duplicating the first page is to just prepend OCR text
        state['raw_text'] = ocr_text + "\n" + raw_text

    # Use the same deterministic helper function on the OCR-enhanced text
    state['landmarks'] = _locate_landmarks_with_re(state.get('raw_text', ''))

    print(f"OCR Landmarks found: {state['landmarks']}")
    return state


def extract_from_pdf_metadata(state: State) -> State:
    """
    (V2) Seeds the state with any metadata found directly in the PDF's internal dictionary.
    This is a fast, non-blocking first pass.
    """
    print("--- NODE: Seeding state from direct PDF metadata ---")
    try:
        paper = pymupdf.open(state['path'])
        paper.close()

        if 'title' in paper.metadata:
            title = paper.metadata['title']
            if title != 'untitled':
                state['title'] = title


        print("--- INFO: Seeding complete. Some fields may be pre-populated. ---")

    except Exception as e:
        print(f"--- ERROR: Could not read PDF for metadata: {e} ---")

    return state


def extract_sliced_metadata(state: State) -> State:
    """
    (V5 - Definitive) Intelligently completes ALL missing metadata from a single, robustly-defined "Extraction Zone".
    It handles out-of-order landmarks and is aware of fields pre-populated by direct PDF extraction.
    """
    print("--- NODE: Sliced Metadata Completion (Full) ---")
    text = state.get('raw_text', '')
    landmarks = state.get('landmarks', {})

    if not text:
        return state

    # --- 1. Create a dictionary of the metadata we need, reflecting the current state ---
    # This will be passed to the LLM so it knows what's missing.
    metadata_to_complete = {
        "title": state.get('title'),
        "authors": state.get('authors'),
        "author_affiliations": state.get('author_affiliations'),
        "publication_date": state.get('publication_date'),
        "year": state.get('year'),
        "journal": state.get('journal'),
        "publisher": state.get('publisher'),
        "keywords": state.get('keywords'),
        "doi": state.get('doi'),
        "abstract": state.get('abstract')
    }
    current_state_json = json.dumps(metadata_to_complete, indent=2)

    # --- 2. Define the single, robust "Extraction Zone" ---
    # The zone ends at the start of the introduction, with a generous fallback.
    page_end = landmarks.get('page_end', -1)
    zone_end_pos = page_end if page_end != -1 else 5000  # Use 5000 chars as a safe fallback
    extraction_zone = text[:zone_end_pos]

    keywords = landmarks.get('keywords_start', -1)
    keywords = text[keywords: keywords + 200] if page_end != -1 else ''  # Use 5000 chars as a safe fallback

    # --- 3. The Definitive Prompt ---
    prompt = prompts.sliced_metadata_prompt(current_state_json, extraction_zone, keywords)


    try:
        response = gemini.invoke(prompt)
        content = response.content.strip("```json\n").strip("`")
        data = json.loads(content)

        # Only update the fields in the state that were originally empty/None
        for key, value in data.items():
            # Check if the key is valid and if the original state for this key was empty.
            # `if not state.get(key)` is a concise way to check for None, "", or [].
            if key in state and not state.get(key) and value:
                state[key] = value

    except (json.JSONDecodeError, KeyError) as e:
        print(f"--- ERROR: Sliced completion failed: {e} ---")

    return state


# --- RELEVANCY & ROUTING NODES ---

def check_paper_relevancy(state: State) -> State:
    """
    A proper LangGraph node that calls an LLM to check for paper relevancy
    and updates the 'relevancy' key in the state.
    """
    print("--- NODE: Checking Paper Relevancy ---")

    # Use the abstract from the state, which was extracted in the previous step
    abstract = state.get('abstract', '')
    if not abstract:
        print("--- WARNING: Abstract is missing. Defaulting to Not Relevant. ---")
        state['relevancy'] = True
        return state

    prompt = prompts.relevancy_check_prompt(abstract)
    try:
        # We can use a faster, cheaper model for this simple classification task.
        # If you have a 'gemini-flash' client, use it here, otherwise 'gemini-1.5-pro' is fine.
        response = gemini.invoke(prompt)
        content = response.content.strip("```json\n").strip("`")
        data = json.loads(content)

        if data.get('relevancy') is True:
            print("--- Paper is Relevant ---")
            state['relevancy'] = True
        else:
            print("--- Paper is Not Relevant ---")
            state['relevancy'] = False

    except Exception as e:
        print(f"--- ERROR: Relevancy check failed: {e}. Defaulting to Relevant. ---")
        state['relevancy'] = True  # Default to false on any error

    return state


def not_relevant_node(state: State) -> State:
    state['relevancy'] = False
    return state


def relevant_node(state: State) -> State:
    state['relevancy'] = True
    return state


# --- PARALLEL ANALYSIS NODES ---

def extract_methodology_and_models(state: State) -> State:
    print("--- NODE: Extracting Methodology & Models ---")
    prompt = prompts.methodology_and_models_prompt(state.get('raw_text', ''))

    try:
        response = gemini.invoke(prompt)
        content = response.content.strip("```json\n").strip("`")
        data = json.loads(content)
        for key, value in data.items():
            if key in state and state.get(key) is None: state[key] = value
    except Exception as e:
        print(f"--- ERROR: Methodology extraction failed: {e} ---")
    return state


def extract_analysis_and_findings(state: State) -> State:
    print("--- NODE: Extracting Analysis & Findings ---")
    prompt = prompts.analysis_and_findings_prompt(state.get('raw_text', ''))

    try:
        response = gemini.invoke(prompt)
        content = response.content.strip("```json\n").strip("`")
        data = json.loads(content)
        for key, value in data.items():
            if key in state and state.get(key) is None: state[key] = value
    except Exception as e:
        print(f"--- ERROR: Analysis extraction failed: {e} ---")
    return state


def extract_dataset_properties(state: State) -> State:
    print("--- NODE: Extracting Dataset Properties ---")
    prompt = prompts.dataset_properties_prompt(state.get('raw_text', ''))

    try:
        response = gemini.invoke(prompt)
        content = response.content.strip("```json\n").strip("`")
        data = json.loads(content)
        for key, value in data.items():
            if key in state and state.get(key) is None: state[key] = value
    except Exception as e:
        print(f"--- ERROR: Dataset extraction failed: {e} ---")
    return state


def extract_experimental_setup(state: State) -> State:
    print("--- NODE: Extracting Experimental Setup ---")
    prompt = prompts.experimental_setup_prompt(state.get('raw_text', ''))

    try:
        response = gemini.invoke(prompt)
        content = response.content.strip("```json\n").strip("`")
        data = json.loads(content)
        for key, value in data.items():
            if key in state and state.get(key) is None: state[key] = value
    except Exception as e:
        print(f"--- ERROR: Experiment extraction failed: {e} ---")
    return state


def dummy_node(state: State) -> State:
    """A simple node that does nothing but pass the state through, used for joining."""
    print("--- NODE: Joining parallel branches ---")
    return state