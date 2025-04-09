import asyncio
import os
import uuid
from pathlib import Path
from typing import Dict, List

import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from agents import Officer, ReConstructor
from constants import CLAIM_FORM_PATH, EMPLOYMENT_FORM_PATH, TEMP_DIR
from document_processor import DocumentProcessor
from image_transcriber import ImageTranscriber
from templates.prompt_templates import (
    LLM_PROMPT_CHECKER,
    LLM_PROMPT_OFFICER,
    LLM_PROMPT_RECONSTRUCTOR,
)
from utils.helpers import (
    aed_to_usd,
    find_missing_keys,
    inject_flattened_values,
    json_to_markdown,
    read_json_file,
    txt2md_converter,
)
from utils.utils import PDF2MD

load_dotenv()

st.set_page_config(layout="wide")

llm = ChatOpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    model="gpt-4o",
    stream_usage=True,
)

reconstructor = ReConstructor(
    llm=llm, actions=[aed_to_usd], prompt=LLM_PROMPT_RECONSTRUCTOR
)
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

    results, missing_pts, conflict_pts, incorrect_claim = (
        await processor.process_documents(file_paths)
    )
    missing_keys = find_missing_keys(schema=JSON_SCHEMA, data=results)
    if incorrect_claim:
        # Adding claim_value ❌ to missing keys to enable updating it
        print("adding claim_value ❌ to missing keys to enable updating it ")
        missing_keys += ["claim_details.claim_value"]

    print(f"missing keys: 2 {missing_keys}")
    st.session_state.summary = json_to_markdown(results)
    st.session_state.summary_json = results

    return results, missing_keys, missing_pts, conflict_pts


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
            results, missing_keys, missing_pts, conflict_pts = loop.run_until_complete(
                analyze_documents(uploaded_files, particular_of_claims)
            )

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
                        {
                            "role": "assistant",
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
                label="🗨️ Your Message",
                placeholder="Write your input...",
                key="user_input",
            )

        with button_col:
            st.markdown("<div style='margin-top: 30px;'>", unsafe_allow_html=True)
            chat_submitted = st.form_submit_button(label="➤")
            st.markdown("</div>", unsafe_allow_html=True)

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
                reconstructor.reconstruct(user_input, st.session_state["missing_keys"])
            )
            print("RECONSTRUCTOR OUTPUT:")
            print("=====")
            print(filled_dict)
            print("=====")
            if isinstance(filled_dict, dict):
                results = inject_flattened_values(
                    filled_dict, st.session_state.summary_json
                )
                # results = safely_fix_claim_value(results)
                st.session_state.summary_json = results
                st.session_state.summary = json_to_markdown(results)

                missing_keys = find_missing_keys(schema=JSON_SCHEMA, data=results)
                st.session_state["missing_keys"] = missing_keys
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

with col2:
    st.subheader("📑 Extracted Document Information")
    st.write(st.session_state.summary)
