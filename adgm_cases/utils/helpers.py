import re
import json
import uuid
from typing import List
from copy import deepcopy
import pymupdf4llm


def gen_file_id(length=4):
    return uuid.uuid4().hex[:length]


def read_json_file(file_path):
    """
    Reads a JSON file and returns the data as a Python dictionary.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The contents of the JSON file as a dictionary.
    """
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except json.JSONDecodeError:
        print("Error: The file is not a valid JSON.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def cleaning_md_4llm(text: str) -> str:

    clean_lines = []

    for line in text.splitlines():
        if line == "-----":
            continue
        if line.startswith("**"):
            line = line.replace("*", "").replace("_", "")
            line = f"### {line}"
        clean_lines.append(line)

    return "\n".join(clean_lines)


async def read_pdf_text(file_path):
    """
    Reads text from a PDF file and returns the extracted text as a string.

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        str: The text extracted from the PDF file.
    """
    try:
        content = pymupdf4llm.to_markdown(file_path)
        return cleaning_md_4llm(content)
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def read_multiple_pdfs(file_paths: List[str]):
    """
    Reads text from multiple PDF files and returns the combined content as a single string.

    Args:
        file_paths (list): A list of file paths for the PDFs.

    Returns:
        str: The combined text extracted from all PDF files.
    """
    combined_content = ""

    for file_path in file_paths:
        try:
            content = pymupdf4llm.to_markdown(file_path)  # Extracts content from PDF
            cleaned_content = cleaning_md_4llm(content)  # Clean the extracted content
            combined_content += (
                cleaned_content + "\n\n" + "=====" * 10 + "\n\n"
            )  # Append the cleaned content
        except FileNotFoundError:
            print(f"Error: The file at {file_path} was not found.")
        except Exception as e:
            print(f"An error occurred while processing {file_path}: {e}")

    return combined_content.strip()  # Return the concatenated content


def aed_to_usd(aed_amount: float):
    """
    Converts AED to USD using the fixed exchange rate.

    Args:
        aed_amount (float): The amount in AED.

    Returns:
        float: The equivalent amount in USD.
    """
    # Fixed conversion rate (1 USD = 3.6725 AED)
    conversion_rate = 1 / 3.6725  # Convert AED to USD

    return aed_amount * conversion_rate


def convert_to_markdown(case_dicts, include_json=True):
    """
    Convert case dictionaries to Markdown format.
    If include_json is True, includes 'Structured JSON Output' block.
    """
    markdown_output = []

    for idx, case in enumerate(case_dicts):
        description = case.get("description", "")
        classification = case.get("classification", "")
        json_data = case.get("json", "")

        markdown = f"""\
### Document {idx+1} / {len(case_dicts)}
**Classification:** `{classification}`
**Description:**
{description}
"""

        if include_json:
            markdown += f"""

##### **Structured JSON Output:**
```json
{json_data}
```"""

        markdown_output.append(markdown.strip())

    return "\n\n---\n\n".join(markdown_output)


def convert_documents_ids_to_markdown(documents: list[dict]) -> str:
    """
    Converts a list of document data dicts into a readable Markdown format.

    Each document_data dict is expected to have 'file_id' and 'description' keys.
    """
    markdown_lines = ["# Document Descriptions\n"]

    for i, doc in enumerate(documents, 1):
        file_id = doc.get("file_id", "Unknown ID")
        description = doc.get("description", "No description available.")

        markdown_lines.append(f"## Document {i}: `{file_id}`\n")
        markdown_lines.append(f"{description}\n")

    return "\n".join(markdown_lines)


def find_missing_keys(schema: dict, data: dict, prefix=""):
    missing = []

    if isinstance(schema, dict):
        for key, schema_val in schema.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if key not in data:
                # If the key is missing at all, report all its leaf paths
                missing.extend(find_all_leaf_paths(schema_val, full_key))
            else:
                data_val = data[key]

                if isinstance(schema_val, dict):
                    if not isinstance(data_val, dict):
                        missing.extend(find_all_leaf_paths(schema_val, full_key))
                    else:
                        missing.extend(
                            find_missing_keys(schema_val, data_val, full_key)
                        )

                elif isinstance(schema_val, list):
                    if isinstance(schema_val[0], dict):  # list of dicts
                        if not data_val:  # empty list
                            missing.extend(find_all_leaf_paths(schema_val[0], full_key))
                        else:
                            for item in data_val:
                                missing.extend(
                                    find_missing_keys(schema_val[0], item, full_key)
                                )
                    else:
                        # list of primitives (e.g., strings)
                        if not data_val:
                            missing.append(full_key)

                else:
                    # primitive leaf node
                    if data_val in ("", None):
                        missing.append(full_key)

    return missing


def find_all_leaf_paths(schema_part, prefix=""):
    missing = []

    if isinstance(schema_part, dict):
        for key, val in schema_part.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(val, dict):
                missing.extend(find_all_leaf_paths(val, full_key))
            elif isinstance(val, list):
                if val and isinstance(val[0], dict):
                    missing.extend(find_all_leaf_paths(val[0], full_key))
                else:
                    missing.append(full_key)
            else:
                missing.append(full_key)

    return missing


def inject_flattened_values(dotted_data: dict, generated_data: dict) -> dict:
    """
    Inserts values from a flat dictionary with dotted keys into a nested dictionary.
    Automatically creates intermediate dictionaries/lists. Defaults to index 0 for list references.
    """

    def set_value(path_parts, value, current):
        for i, part in enumerate(path_parts):
            # Detect if we're at the last part of the path
            is_last = i == len(path_parts) - 1

            # Handle possible list key or plain dict key
            if part in current and isinstance(current[part], list):
                # Default to index 0 if it's a list
                if not current[part]:
                    current[part].append({})

                current = current[part][0]
            elif "[" in part and "]" in part:
                # Handle explicit list index (e.g. individuals[1])
                key, idx = part.rstrip("]").split("[")
                idx = int(idx)

                if key not in current or not isinstance(current[key], list):
                    current[key] = []

                while len(current[key]) <= idx:
                    current[key].append({})

                if is_last:
                    current[key][idx] = value
                else:
                    current = current[key][idx]
            else:
                if is_last:
                    current[part] = value
                else:
                    if part not in current or not isinstance(
                        current[part], (dict, list)
                    ):
                        current[part] = {}
                    current = current[part]

    updated = deepcopy(generated_data)
    if isinstance(dotted_data, dict):
        for dotted_key, value in dotted_data.items():
            path_parts = dotted_key.split(".")
            set_value(path_parts, value, updated)

    return updated


def clean_json_string(text: str) -> str:
    # 1. Remove single-line comments (//), ignoring http:// or https://
    def remove_inline_comments(text):
        return re.sub(r"(?<!https:)(?<!http:)//.*", "", text)

    # 2. Remove block comments (/* ... */)
    def remove_block_comments(text):
        return re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)

    # 3. Remove trailing commas before closing } or ]
    def remove_trailing_commas(text):
        return re.sub(r",\s*(\]|\})", r"\1", text)

    # 4. Replace invalid literals like undefined, NaN, Infinity
    def replace_non_json_literals(text):
        return (
            text.replace("undefined", "null")
            .replace("NaN", "null")
            .replace("Infinity", "null")
        )

    # # 5. Optionally replace single quotes with double quotes (CAREFUL!)
    # def replace_single_quotes(text):
    #     return re.sub(r"(?<!\\)'", '"', text)

    # Apply the cleaning steps in sequence
    text = remove_inline_comments(text)
    text = remove_block_comments(text)
    text = remove_trailing_commas(text)
    text = replace_non_json_literals(text)
    # text = replace_single_quotes(text)

    return text.strip()


def safe_get(data, keys, default="N/A"):
    try:
        for key in keys:
            data = data.get(key, {})
        return data if data else default
    except Exception:
        return default


def json_to_markdown(data):
    markdown = ""

    # Claimant
    markdown += f"### Claimant\n"
    markdown += (
        f"- **First Name:** {safe_get(data.get('claimant', {}), ['first_name'])}\n"
    )
    markdown += (
        f"- **Last Name:** {safe_get(data.get('claimant', {}), ['last_name'])}\n"
    )
    additional_claimants = data.get("claimant", {}).get("additional_claimants", [])
    if additional_claimants:
        markdown += f"- **Additional Claimants:**\n"
        for claimant in additional_claimants:
            markdown += f"  - {safe_get(claimant, ['full_name'])}\n"

    # Defendant
    markdown += f"\n### Defendant\n"
    markdown += (
        f"- **First Name:** {safe_get(data.get('defendant', {}), ['first_name'])}\n"
    )
    additional_defendants = data.get("defendant", {}).get("additional_defendants", [])
    if additional_defendants:
        markdown += f"- **Additional Defendants:**\n"
        for defendant in additional_defendants:
            markdown += f"  - {safe_get(defendant, ['full_name'])}\n"

    # Claimant Filing Details
    filing = data.get("claimant_filing_details", {})
    markdown += f"\n### Claimant Filing Details\n"
    rep_type = safe_get(filing, ["representation_type"])
    markdown += f"- **Representation Type:** {rep_type}\n"
    if rep_type == "Legal Representative":
        rep = filing.get("legal_representative", {})
        markdown += f"  - **Legal Representative:** {safe_get(rep, ['name'])}\n"
        markdown += f"  - **Law Firm:** {safe_get(rep, ['firm'])}\n"
        markdown += f"  - **Contact Name:** {safe_get(rep, ['contact_name'])}\n"
        markdown += (
            f"  - **Contact Telephone:** {safe_get(rep, ['contact_telephone'])}\n"
        )
        markdown += f"  - **Contact Email:** {safe_get(rep, ['contact_email'])}\n"

    # Defendant Address for Service
    markdown += f"\n### Defendant Address for Service\n"
    address_service = data.get("defendant_address_for_service", {})
    individuals = address_service.get("individuals", [])
    if individuals:
        markdown += f"- **Individuals:**\n"
        for individual in individuals:
            markdown += f"  - **Home/Work Address:** {safe_get(individual, ['home_or_work_address'])}\n"
            markdown += f"  - **Email:** {safe_get(individual, ['email'])}\n"
            markdown += f"  - **Mobile:** {safe_get(individual, ['mobile'])}\n"
    companies = address_service.get("companies", [])
    if companies:
        markdown += f"- **Companies:**\n"
        for company in companies:
            markdown += f"  - **Registered Office Address:** {safe_get(company, ['registered_office_address'])}\n"
            markdown += f"  - **Email:** {safe_get(company, ['email'])}\n"
            markdown += f"  - **Mobile:** {safe_get(company, ['mobile'])}\n"

    # Nature and Value of Claim
    claim = data.get("nature_and_value_of_claim", {})
    markdown += f"\n### Nature and Value of Claim\n"
    markdown += f"- **Nature of Claim:** {safe_get(claim, ['nature_of_claim'])}\n"
    markdown += f"- **Claim Value (USD):** {safe_get(claim, ['claim_value_usd'])}\n"
    markdown += f"- **Interest Details:** {safe_get(claim, ['interest_details'])}\n"

    # Final Orders Sought
    markdown += f"\n### Final Orders Sought\n"
    orders = data.get("final_orders_sought", [])
    if orders:
        for order in orders:
            markdown += f"- {order or 'N/A'}\n"
    else:
        markdown += f"- N/A\n"

    # Particulars of Claim
    particulars = data.get("particulars_of_claim", {})
    markdown += f"\n### Particulars of Claim\n"
    details = particulars.get("details", [])
    if details:
        markdown += f"- **Details:**\n"
        for detail in details:
            markdown += f"  - {detail or 'N/A'}\n"
    docs = particulars.get("supporting_documents", [])
    if docs:
        markdown += f"- **Supporting Documents:**\n"
        for doc in docs:
            markdown += f"  - {doc or 'N/A'}\n"

    # Employment Terms
    employment = data.get("employment_terms", {})
    remuneration = employment.get("rate_of_remuneration", {})
    markdown += f"\n### Employment Terms\n"
    markdown += f"- **Employment Agreement Attached:** {safe_get(employment, ['employment_agreement_attached'])}\n"
    markdown += f"- **Rate of Remuneration:** {safe_get(remuneration, ['currency'])} {safe_get(remuneration, ['amount'])} ({safe_get(remuneration, ['payment_frequency'])})\n"

    # Statement of Grounds
    markdown += f"\n### Statement of Grounds\n"
    markdown += f"- **Jurisdictional Grounds:** {safe_get(data.get('statement_of_grounds', {}), ['jurisdictional_grounds'])}\n"

    # Mediation
    mediation = data.get("mediation", {})
    markdown += f"\n### Mediation\n"
    markdown += f"- **Opt-in for Mediation:** {safe_get(mediation, ['opt_in'])}\n"
    markdown += f"- **Reason if No:** {safe_get(mediation, ['reason_if_no'])}\n"

    return markdown


def txt2md_converter(text: str) -> str:
    markdown_lines = []
    lines = text.strip().splitlines()

    # Compile the monetary pattern outside the loop for efficiency
    money_pattern = re.compile(r"(AED|USD|SAR)?\s?[\d{1,3},]*\d+\.\d{2}")

    for i, line in enumerate(lines):
        original_line = line.strip()

        # Skip empty lines
        if not original_line:
            continue

        try:
            # Detect monetary value
            is_money = bool(money_pattern.search(original_line))

            # Header Rule: 2-5 words, no ending punctuation, standalone line
            if (
                2 <= len(original_line.split()) <= 5
                and not original_line.endswith((".", ":", "..."))
                and not any(
                    original_line.startswith(prefix)
                    for prefix in ["-", "○", "•", "*", "1 ", "2 ", "3 "]
                )
            ):
                markdown_lines.append(f"### {original_line}")
                continue

            # Bullet/Numbered List Rule (with bullet-like symbols at the start)
            if original_line.lstrip().startswith(("○", "-", "•", "*")):
                content = original_line.lstrip("○-•* ").strip()
                markdown_lines.append(f"- {content}")
                continue

            # Numbered List with value at end (Updated regex to handle optional currency and numbers)
            numbered_match = re.match(
                r"^(\d+)\s+(.*?)(\s*(AED|USD|SAR)?\s?[\d{1,3},]*\d+\.\d{2})?$",
                original_line,
            )
            if numbered_match:
                groups = numbered_match.groups()
                idx = groups[0]
                item = groups[1].strip()
                amount = groups[4] if len(groups) > 4 and groups[4] else None

                if amount:
                    markdown_lines.append(f"{idx}. {item} **{amount.strip()}**")
                else:
                    markdown_lines.append(f"{idx}. {item}")
                continue

            # Total lines (Grand Total or Total with a currency value)
            if re.match(
                r"^\s*(-\s*)?(Total|Grand Total)\b.*?[\d{1,3},]*\d+\.\d{2}",
                original_line,
                re.IGNORECASE,
            ):
                markdown_lines.append(f"- **{original_line}**")
                continue

            # Generic money match: bold the currency-like values in any sentence
            if is_money:
                modified_line = money_pattern.sub(
                    lambda m: f"**{m.group(0)}**", original_line
                )
                markdown_lines.append(modified_line)
                continue

            # Default case: keep as-is
            markdown_lines.append(original_line)

        except Exception as e:
            # In case any error occurs, log it and continue
            print(f"[ERROR: Could not process line: {original_line}]: \n\n {e} \n")
            return text

    return "\n".join(markdown_lines)
