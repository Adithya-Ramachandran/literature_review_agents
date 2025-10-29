def sliced_metadata_prompt(current_state_json: str, extraction_zone: str, keywords: str) -> str:
    return f"""
    You are an expert AI assistant that completes a metadata record for a scientific paper.

    **CRITICAL INSTRUCTIONS:**
    1.  Below is the "CURRENT METADATA" record. Your primary task is to fill in any fields that are currently `null`, empty `""`, or an empty list `[]`.
    2.  Use the "EXTRACTION ZONE TEXT" provided as your single source of truth. This text is the first part of the paper.
    3.  The metadata elements (title, abstract, keywords) may appear in an unusual, non-linear order. Search the entire zone.
    4.  DO NOT change or overwrite fields in the metadata that already contain valid information.
    5.  Your final output must be ONLY the completed JSON object.

    **CURRENT METADATA (Fill in the blanks):**
    {current_state_json}

    **EXTRACTION ZONE TEXT (Source of truth):**
    ---
    {extraction_zone}


    Keywords: {keywords}
    ---
    """


def relevancy_check_prompt(abstract: str) -> str:
    return f"""
    Is the paper with this abstract relevant to 'Power System Management - Machine Learning for fault detection, Islanding detection, fault classification, fault localisation '? 
    Respond with only a JSON object: {{\"relevancy\": true or false}}. 
    Abstract: --- {abstract} ---
    """


def methodology_and_models_prompt(raw_text: str) -> str:
    return f"""
    From the paper text, extract the proposed model name, a detailed methodology summary, the unique selling proposition (USP), and a list of all empirically evaluated methods (proposed + baselines). Output ONLY the JSON.
    JSON: {{"proposed_model_name":"", "methodology":"", "usp":"", "experimental_methods":[]}}
    Paper Text: --- {raw_text} ---
    """


def analysis_and_findings_prompt(raw_text: str) -> str:
    return f"""
    From the paper text, extract the core analysis.

    **CRITICAL INSTRUCTIONS:**
    - **problem_statement:** Provide a CONCISE "Focus" statement (e.g., "Fault detection in transmission lines", "Islanding detection in PV-based microgrids").
    - **main_findings:** Summarize the key quantitative results (e.g., "Achieved 99% accuracy with <2ms detection time").

    Output ONLY the JSON.
    JSON: {{"problem_statement":"", "main_findings":"", "limitations":"", "future_work":""}}
    Paper Text: --- {raw_text} ---
    """




def experimental_setup_prompt(raw_text: str) -> str:
    return f"""
    From the paper text, extract the experimental setup details.

    **CRITICAL INSTRUCTIONS:**
    - **resolution:** Look specifically for sampling frequency ($f_s$) or time intervals (e.g., "40 MHz", "2 kHz", "15 minutes"). If not found, explicitly state "unspecified".
    - **features_used:** explicitly mention the signal domain if listed (e.g., "phasor domain V/I", "waveform current", "RMS images").
    - **metrics:** List ALL quantitative results mentioned in the abstract or conclusion (accuracy %, detection time in ms, MAPE).

    Output ONLY the JSON.
    JSON: {{"train_test_split":"", "horizon":"", "resolution":"", "features_used":[], "data_preprocessing":[], "metrics":[], "data_availability":"", "code_availability":""}}
    Paper Text: --- {raw_text} ---
    """


def dataset_properties_prompt(raw_text: str) -> str:
    return f"""
    From the paper text, extract the dataset's key properties.

    **CRITICAL INSTRUCTIONS:**
    - **source_type:** Specify if it is "Real-world", "Simulated", or "Synthetic". IF SIMULATED, name the platform (e.g., "Simulink", "PowerFactory", "OpenDSS").
    - **granularity_scale:** describe the scope (e.g., "IEEE 39-bus system", "Real 20kV network in Basque Country").
    - **num_data_points:** Look for total samples, scenarios, or event recordings (e.g., "5000 fault cases", "181 COMTRADE events").

    Output ONLY the JSON.
    JSON: {{"dataset_name":"", "source_type":"", "granularity_scale":"", "dataset_duration":"", "num_data_points":"", "data_description":""}}
    Paper Text: --- {raw_text} ---
    """