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
    Is the paper with this abstract relevant to 'Time Series Forecasting'? 
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
    From the paper text, extract the problem statement, main findings, author-stated limitations, and future work. Output ONLY the JSON.
    JSON: {{"problem_statement":"", "main_findings":"", "limitations":"", "future_work":""}}
    Paper Text: --- {raw_text} ---
    """


def dataset_properties_prompt(raw_text: str) -> str:
    return f"""
    From the paper text, extract the dataset's name, source type (real/simulated), granularity/scale, total duration, number of data points, and a brief description. Output ONLY the JSON.
    JSON: {{"dataset_name":"", "source_type":"", "granularity_scale":"", "dataset_duration":"", "num_data_points":"", "data_description":""}}
    Paper Text: --- {raw_text} ---
    """


def experimental_setup_prompt(raw_text: str) -> str:
    return f"""
    From the paper text, extract the experimental setup details: train/test split, forecast horizon, data resolution, features used, preprocessing steps, evaluation metrics, and data/code availability. Output ONLY the JSON.
    JSON: {{"train_test_split":"", "horizon":"", "resolution":"", "features_used":[], "data_preprocessing":[], "metrics":[], "data_availability":"", "code_availability":""}}
    Paper Text: --- {raw_text} ---
    """