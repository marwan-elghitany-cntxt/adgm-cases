import asyncio
import os
import textwrap
from typing import Dict, List
import uuid
import openai
from fpdf import FPDF
from io import BytesIO

import streamlit as st
from constants import CLAIM_FORM_PATH, EMPLOYMENT_FORM_PATH, TEMP_DIR
from image_transcriber import ImageTranscriber
from langchain_openai import ChatOpenAI
from document_processor import DocumentProcessor
from utils.helpers import (
    find_missing_keys,
    inject_flattened_values,
    json_to_markdown,
    read_json_file,
    txt2md_converter,
)
from agents import Officer, ReConstructor
from templates.prompt_templates import (
    LLM_PROMPT_CHECKER,
    LLM_PROMPT_CLASSIFIER,
    LLM_PROMPT_COMBINER,
    LLM_PROMPT_CONFLICT,
    LLM_PROMPT_DESCRIPER,
    LLM_PROMPT_EXTRACTOR,
    LLM_PROMPT_MISSING_DETECTOR,
    LLM_PROMPT_OFFICER,
    LLM_PROMPT_RECONSTRUCTOR,
    LLM_PROMPT_REVISOR,
    LLM_PROMPT_UNMENTIONED_DETECTOR,
)
from pathlib import Path
import asyncio
import os
import uuid
from typing import Dict, List
from pathlib import Path

import streamlit as st
from langchain_openai import ChatOpenAI

from image_transcriber import ImageTranscriber
from document_processor import DocumentProcessor
from agents import Officer, ReConstructor
from templates.prompt_templates import (
    LLM_PROMPT_CLASSIFIER,
    LLM_PROMPT_COMBINER,
    LLM_PROMPT_DESCRIPER,
    LLM_PROMPT_EXTRACTOR,
    LLM_PROMPT_OFFICER,
    LLM_PROMPT_RECONSTRUCTOR,
    LLM_PROMPT_REVISOR,
)
from utils.utils import PDF2MD

from dotenv import load_dotenv

load_dotenv()

st.set_page_config(layout="wide")

llm = ChatOpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    model="gpt-4o",
    stream_usage=True,
)

reconstructor = ReConstructor(llm=llm, actions=[], prompt=LLM_PROMPT_RECONSTRUCTOR)
officer = Officer(llm=llm, actions=[], prompt=LLM_PROMPT_OFFICER)
checker = Officer(llm=llm, actions=[], prompt=LLM_PROMPT_CHECKER)

# Streamlit setup
st.title("ADGM E-Courts Claim Assistant")

# Sidebar toggle
form_type = st.sidebar.radio("Select Form Type", ("Employment Form", "Claim Form"))
form_path = EMPLOYMENT_FORM_PATH if form_type == "Employment Form" else CLAIM_FORM_PATH
JSON_SCHEMA = read_json_file(form_path)

# Initialize session state
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("summary", "Upload documents to extract information.")
st.session_state.setdefault("summary_json", {})
st.session_state.setdefault("documents", [])
st.session_state.setdefault("session_id", f"{TEMP_DIR}/{str(uuid.uuid4())}")
st.session_state.setdefault("missing_keys", [])
st.markdown(
    """
    <style>
    .stButton > button {
        background-color: #FF6347;  /* Change to your desired color */
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: #FF4500;  /* Hover color */
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def save_claims_to_text_file(text: str, file_path: str = "particular_of_claims.txt"):
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(text)


async def extract_text_from_pdfs(files: List[object]):
    extracted_texts = []
    transcriber = ImageTranscriber(
        base_url=os.environ["BASE_URL"],
        model_name=os.environ["MODEL_NAME"],
        api_key=os.environ["API_KEY"],
    )

    for file in files:
        if file.name in [doc["filename"] for doc in st.session_state.documents]:
            continue

        progress_bar = st.progress(0)
        file_path = PDF2MD.save_uploaded_file(file)
        images_paths = PDF2MD.pdf_to_images(
            pdf_path=file_path,
            output_folder=os.path.join(
                st.session_state["session_id"], Path(file.name).stem
            ),
        )
        transcriptions = await transcriber.run(
            imgs_path=images_paths, progress_bar=progress_bar
        )
        extracted_texts.append(transcriptions)

    return extracted_texts


async def analyze_documents(files, claims_text: str):

    os.makedirs(st.session_state.session_id, exist_ok=True)

    # # new_files = [
    # #     file
    # #     for file in files
    # #     if file.name not in [doc["filename"] for doc in st.session_state.documents]
    # # ]

    # if not new_files:
    #     return None, None

    file_paths = []
    for file in files:
        file_path = PDF2MD.save_uploaded_file(st.session_state.session_id, file)
        file_paths.append(file_path)
        st.session_state.documents.append({"filename": file.name})

    # Save claims text to a .txt file in session dir
    if claims_text:
        claims_path = os.path.join(st.session_state.session_id, "claims_text.txt")
        with open(claims_path, "w", encoding="utf-8") as f:
            f.write(txt2md_converter(claims_text.strip()))
        file_paths.append(claims_path)
        st.session_state.documents.append({"filename": "claims_text.txt"})

    st.session_state.summary = f"Uploaded {len(files)} new document(s). Processing .."

    processor = DocumentProcessor(
        llm=llm,
        describer_actions=[],
        extractor_actions=[],
        describer_prompt=LLM_PROMPT_DESCRIPER,
        extractor_prompt=LLM_PROMPT_EXTRACTOR,
        classifier_prompt=LLM_PROMPT_CLASSIFIER,
        combiner_prompt=LLM_PROMPT_COMBINER,
        revisor_prompt=LLM_PROMPT_REVISOR,
        missing_docs_prompt=LLM_PROMPT_MISSING_DETECTOR,
        poclaims_conflicts_prompt=LLM_PROMPT_CONFLICT,
        not_refrenced_docs_prompt=LLM_PROMPT_UNMENTIONED_DETECTOR,
        json_structure=JSON_SCHEMA,
    )

    results, missing_pts, cfl_pts = await processor.process_documents(file_paths)
    missing_keys = find_missing_keys(schema=JSON_SCHEMA, data=results)

    st.session_state.summary = json_to_markdown(results)
    st.session_state.summary_json = results

    return results, missing_keys, missing_pts, cfl_pts


async def ask_llm(messages: List[Dict], is_checker=False):
    if is_checker:
        return await checker.serve(messages)
    return await officer.serve(messages)


# Layout
col1, col2 = st.columns([2, 1])

with col1:

    st.subheader("Your Case Details")
    particular_of_claims = st.text_area("Enter details of the claim", height=150)

    st.subheader("📂 Upload Your Supporting Documents")
    uploaded_files = st.file_uploader(
        "Upload multiple PDFs", type=["pdf"], accept_multiple_files=True
    )

    # 🔘 Submit Button to trigger processing
    submit = st.button("Submit for Analysis")

    if submit:
        print("Submit Button Pressed !!")
        # print(f"{uploaded_files=}")
        # print(f"{particular_of_claims.strip()=}")
        print("Submit Button Pressed !! DONE")

        if uploaded_files and particular_of_claims.strip():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results, missing_keys, missing_pts, cfl_pts = loop.run_until_complete(
                analyze_documents(uploaded_files, particular_of_claims)
            )

            if missing_keys:
                st.session_state.chat_history.extend(
                    [
                        {"role": "system", "content": f"Missing Keys: {missing_keys}"},
                        {"role": "system", "content": f"Conflicts found: {cfl_pts}"},
                        {
                            "role": "system",
                            "content": f"Missing documents to be uploaded: {missing_pts}",
                        },
                        # {"role": "system", "content": f"Documents already Uploaded but user didn't reference through the his summary: {nrf_pts}"},
                    ]
                )
                llm_reply = asyncio.run(
                    ask_llm(st.session_state.chat_history, is_checker=True)
                )
                st.session_state.chat_history.append(
                    {"role": "ai", "content": llm_reply}
                )
                st.session_state["missing_keys"] = missing_keys
        else:
            st.warning("Please enter claim details and upload at least one PDF.")

    st.subheader("Chat Interface")
    with st.form("chat_form", clear_on_submit=True):
        input_col, button_col = st.columns([5, 1])  # Adjust ratio as needed

        with input_col:
            user_input = st.text_input(
                label="",
                placeholder="Write your input...",
                key="user_input"
            )

        with button_col:
            st.markdown("<div style='margin-top: 30px;'>", unsafe_allow_html=True)
            chat_submitted = st.form_submit_button(label="➤")
            st.markdown("</div>", unsafe_allow_html=True)


    if user_input and chat_submitted:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        # No need for more keys
        if not st.session_state["missing_keys"]:
            st.session_state.chat_history.append(
                {"role": "system", "content": f"No Missing Keys Found!"}
            )
            # Chat normally
            llm_reply = asyncio.run(ask_llm(st.session_state.chat_history))
            st.session_state.chat_history.append({"role": "ai", "content": llm_reply})
        else:
            filled_dict = asyncio.run(
                reconstructor.reconstruct(user_input, st.session_state["missing_keys"])
            )
            results = inject_flattened_values(
                filled_dict, st.session_state.summary_json
            )
            st.session_state.summary_json = results
            st.session_state.summary = json_to_markdown(results)

            missing_keys = find_missing_keys(schema=JSON_SCHEMA, data=results)
            st.session_state["missing_keys"] = missing_keys
            # Still exist Missing Keys after the user input, add to history and generate reply
            if missing_keys:
                st.session_state.chat_history.append(
                    {
                        "role": "system",
                        "content": f"Updated Missing Keys: {missing_keys}",
                    }
                )
                llm_reply = asyncio.run(ask_llm(st.session_state.chat_history))
                st.session_state.chat_history.append(
                    {"role": "ai", "content": llm_reply}
                )
            # Or else update the model that no other missing keys needed
            else:
                st.session_state.chat_history.append(
                    {"role": "system", "content": f"No Other Missing Keys Found!"}
                )
                llm_reply = asyncio.run(ask_llm(st.session_state.chat_history))
                st.session_state.chat_history.append(
                    {"role": "ai", "content": llm_reply}
                )

    if st.session_state.chat_history:
        st.write(st.session_state.chat_history[-1]["content"])

with col2:
    st.subheader("📑 Extracted Document Information")
    st.write(st.session_state.summary)
