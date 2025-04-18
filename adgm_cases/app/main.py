import asyncio
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from time import sleep
import uuid
from pathlib import Path
from typing import Dict, List

from loguru import logger
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from agents import Officer, ReConstructor, Summarizer
from constants import CACHED_VALUES, CLAIM_FORM, EMPLOYMENT_FORM, TEMP_DIR
from document_processor import DocumentProcessor
from image_transcriber import ImageTranscriber
from templates.prompt_templates import (
    LLM_PROMPT_CHECKER,
    LLM_PROMPT_OFFICER,
    LLM_PROMPT_RECONSTRUCTOR,
    LLM_PROMPT_SUMMARIZER,
)
from utils.helpers import (
    aed_to_usd,
    clean_for_cache,
    find_missing_keys,
    flatten_json2dots,
    inject_flattened_values,
    is_claim_value_updated,
    json_to_markdown,
    txt2md_converter,
)
from utils.utils import PDF2MD

load_dotenv()

st.set_page_config(layout="wide")

llm = ChatOpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    model="gpt-4o",
    stream_usage=True,
    temperature=0.1,
)

reconstructor = ReConstructor(
    llm=llm, actions=[aed_to_usd], prompt=LLM_PROMPT_RECONSTRUCTOR
)
officer = Officer(llm=llm, actions=[], prompt=LLM_PROMPT_OFFICER)
checker = Officer(llm=llm, actions=[], prompt=LLM_PROMPT_CHECKER)
summarizer = Summarizer(llm=llm, prompt=LLM_PROMPT_SUMMARIZER)

# Streamlit setup
st.title("ADGM E-Courts Claim Assistant")

# Sidebar toggle
# form_type = st.sidebar.radio("Select Form Type", ("Employment Form", "Claim Form"))
JSON_SCHEMA = EMPLOYMENT_FORM #if form_type == "Employment Form" else CLAIM_FORM
# JSON_SCHEMA = read_json_file(form_path)

# Initialize session state
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("summary", "Upload documents to extract information.")
st.session_state.setdefault("summary_json", {})
st.session_state.setdefault("documents", [])
st.session_state.setdefault("session_id", f"{TEMP_DIR}/{str(uuid.uuid4())}")
st.session_state.setdefault("missing_keys", [])
st.session_state.setdefault("all_keys", [])
st.session_state.setdefault("case_summary", "")
st.markdown(
    """
    <style>
    .stButton:nth-child(1) button {
        background-color: #FF6347;
        color: white;
    }
    .stButton:nth-child(2) button {
        background-color: #4682B4;
        color: white;
    }
    .stButton > button {
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        cursor: pointer;
    }
    .stButton:nth-child(1) button:hover {
        background-color: #FF4500;
    }
    .stButton:nth-child(2) button:hover {
        background-color: #4169E1;
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

    processor = DocumentProcessor(llm=llm, json_structure=JSON_SCHEMA)

    results, conflict_pts, incorrect_claim, case_summary = (
        await processor.process_documents(file_paths)
    )
    missing_keys = find_missing_keys(schema=JSON_SCHEMA, data=results)
    if incorrect_claim:
        # Adding claim_value ❌ to missing keys to enable updating it
        logger.info("adding claim_value ❌ to missing keys to enable updating it ")
        missing_keys += ["claim_details.claim_value"]

    return results, missing_keys, conflict_pts, case_summary


async def ask_llm(messages: List[Dict], is_checker=False):
    if is_checker:
        return await checker.serve(messages)
    return await officer.serve(messages)


async def update_summary(case_summary, history):
    return await summarizer.summarize(case_summary, history)


def are_files_cached(files):

    print("are ALL CACHED ?::")
    print([f.name for f in files])
    print(all(file.name in CACHED_VALUES["file_names"] for file in files))

    return all(file.name in CACHED_VALUES["file_names"] for file in files)


def check_cached_values(uploaded_files, particular_of_claims):
    return (
        CACHED_VALUES["particular_of_claims"] == clean_for_cache(particular_of_claims)
    ) and are_files_cached(uploaded_files)


# Layout
col1, col2 = st.columns([2, 1])

with col1:

    st.subheader("Your Case Details")
    particular_of_claims = st.text_area("Enter details of the claim", height=150)

    st.subheader("📂 Upload Your Supporting Documents")
    uploaded_files = st.file_uploader(
        "Upload multiple PDFs", type=["pdf"], accept_multiple_files=True
    )

    # Two buttons side-by-side in the same column
    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        submit = st.button("Submit for Analysis")
    with btn_col2:
        summary_update = st.button("Update Summary")

    if summary_update:
        if st.session_state.case_summary:
            st.session_state.case_summary = asyncio.run(
                update_summary(
                    st.session_state.case_summary, st.session_state.chat_history
                )
            )
        else:
            st.warning("Please Submit a usecase first..")

    if submit:
        if uploaded_files and particular_of_claims.strip():

            results = missing_keys = conflict_pts = case_summary = llm_reply = None

            if check_cached_values(uploaded_files, particular_of_claims):
                sleep(3)
                print("Using the Caching documents")
                results, missing_keys, conflict_pts, case_summary, llm_reply = (
                    CACHED_VALUES["json_result"],
                    CACHED_VALUES["missing_values"],
                    CACHED_VALUES["conflicts"],
                    CACHED_VALUES["case_summary"],
                    CACHED_VALUES["respond"],
                )
            else:
                print("Executing the Pipeline ...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results, missing_keys, conflict_pts, case_summary = (
                    loop.run_until_complete(
                        analyze_documents(uploaded_files, particular_of_claims)
                    )
                )

            all_keys = flatten_json2dots(results)

            if missing_keys:
                st.session_state.chat_history.extend(
                    [
                        {
                            "role": "assistant",
                            "content": f"Missing Keys: {missing_keys}",
                        },
                        {
                            "role": "assistant",
                            "content": f"Conflicts found: {conflict_pts}",
                        },
                    ]
                )
            # Respond
            if not llm_reply:
                llm_reply = asyncio.run(
                    ask_llm(st.session_state.chat_history, is_checker=True)
                )
            st.session_state.chat_history.append({"role": "ai", "content": llm_reply})
            st.session_state["missing_keys"] = missing_keys
            st.session_state["all_keys"] = all_keys
            st.session_state.case_summary = case_summary
            st.session_state.summary = json_to_markdown(results)
            st.session_state.summary_json = results
        else:
            st.warning("Please enter claim details and upload at least one PDF.")

    st.subheader("Chat Interface")
    with st.form("chat_form", clear_on_submit=True):
        input_col, button_col = st.columns([5, 1])  # Adjust ratio as needed

        with input_col:
            user_input = st.text_input(
                label="🗨️ Your Message",
                placeholder="Write your input...",
                key="user_input",
            )

        with button_col:
            st.markdown("<div style='margin-top: 30px;'>", unsafe_allow_html=True)
            chat_submitted = st.form_submit_button(label="➤")
            st.markdown("</div>", unsafe_allow_html=True)

    # Chatting Input
    if user_input and chat_submitted:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        # All Keys are set
        if not st.session_state["missing_keys"]:
            st.session_state.chat_history.append(
                {"role": "assistant", "content": f"No Missing Keys Found!"}
            )
            # Chat normally
            llm_reply = asyncio.run(ask_llm(st.session_state.chat_history))
            st.session_state.chat_history.append({"role": "ai", "content": llm_reply})
        else:
            filled_dict = asyncio.run(
                reconstructor.reconstruct(
                    user_response=user_input,
                    missing_keys=st.session_state["missing_keys"],
                    all_keys=st.session_state["all_keys"],
                )
            )
            logger.info("RECONSTRUCTOR OUTPUT:")
            logger.info("=====")
            logger.info(filled_dict)
            logger.info("=====")
            if isinstance(filled_dict, dict):
                results = inject_flattened_values(
                    filled_dict, st.session_state.summary_json
                )
                st.session_state.summary_json = results
                st.session_state.summary = json_to_markdown(results)

                missing_keys = find_missing_keys(schema=JSON_SCHEMA, data=results)
                if not is_claim_value_updated(results):
                    print("Claim Value still not updated")
                    missing_keys.insert(0, "claim_details.claim_value")
                st.session_state["missing_keys"] = missing_keys
                st.session_state["all_keys"] = flatten_json2dots(results)
                # Still exist Missing Keys after the user input, add to history and generate reply
                if missing_keys:
                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
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
                        {
                            "role": "assistant",
                            "content": f"No Other Missing Keys Found!",
                        }
                    )
                    llm_reply = asyncio.run(ask_llm(st.session_state.chat_history))
                    st.session_state.chat_history.append(
                        {"role": "ai", "content": llm_reply}
                    )
            # Handling JSON exception for Reconstructor
            elif isinstance(filled_dict, str):
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": filled_dict}
                )

    if st.session_state.chat_history:
        st.write(st.session_state.chat_history[-1]["content"])
        if st.session_state.case_summary:
            st.markdown("### Case Summary:")
            st.write(st.session_state.case_summary)


with col2:
    st.subheader("📑 Extracted Document Information")
    st.write(st.session_state.summary)
