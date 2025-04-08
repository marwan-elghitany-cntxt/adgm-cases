import asyncio
from langchain_core.output_parsers import JsonOutputParser
from agents import (
    DocumentDescriber,
    JSONCombiner,
    JSONExtractor,
    Revisor,
)
from utils.helpers import (
    convert_documents_ids_to_markdown,
    convert_to_markdown,
    find_missing_keys,
    gen_file_id,
    inject_flattened_values,
    read_pdf_text,
)


class DocumentProcessor:
    def __init__(
        self,
        llm,
        describer_prompt,
        extractor_prompt,
        classifier_prompt,
        combiner_prompt,
        revisor_prompt,
        # missing_docs_prompt,
        # not_refrenced_docs_prompt,
        # poclaims_conflicts_prompt,
        describer_actions,
        extractor_actions,
        json_structure,
    ):
        self.llm = llm

        self.describer_prompt = describer_prompt
        self.extractor_prompt = extractor_prompt
        self.classifier_prompt = classifier_prompt
        self.combiner_prompt = combiner_prompt
        self.revisor_prompt = revisor_prompt
        # self.missing_docs_prompt = missing_docs_prompt
        # self.not_refrenced_docs_prompt = not_refrenced_docs_prompt
        # self.poclaims_conflicts_prompt = poclaims_conflicts_prompt

        self.describer_actions = describer_actions
        self.extractor_actions = extractor_actions
        self.json_structure = json_structure

    async def _read_document(self, file_path: str) -> dict:
        document = await read_pdf_text(file_path)
        file_id = gen_file_id()
        if not document:
            print(f"Failed to read document in path: {file_path}")
            return {
                "file_id": file_id,
                "file": file_path,
                "error": "Failed to read document",
                "document": None,
            }
        print(f"{file_id}:{document}")
        return {"file": file_path, "file_id": file_id, "document": document}

    async def _describe_document(self, document_data: dict) -> dict:
        if not document_data.get("document"):
            return {
                **document_data,
                "error": document_data.get("error", "No document provided"),
                "description": None,
            }

        describer = DocumentDescriber(
            llm=self.llm,
            actions=self.describer_actions,
            prompt=self.describer_prompt,
        )
        description = await describer.describe(document_data["document"])
        return {**document_data, "description": description}

    async def _classify_document(self, case_documents: list[dict]) -> dict:

        describer = DocumentDescriber(
            llm=self.llm,
            actions=[],
            prompt=self.classifier_prompt,
        )
        case_documents_md = convert_documents_ids_to_markdown(case_documents)
        classification = await describer.describe(case_documents_md)
        print("---")
        print(classification)
        print("---")
        return await JsonOutputParser().ainvoke(classification)

    async def _not_ref_documents(self, case_documents: list[dict]) -> dict:

        describer = DocumentDescriber(
            llm=self.llm,
            actions=[],
            prompt=self.not_refrenced_docs_prompt,
        )
        case_documents_md = convert_documents_ids_to_markdown(case_documents)
        result = await describer.describe(case_documents_md)
        print("---Not Referenced---")
        print(result)
        print("---")
        return result

    async def _conflicts_documents(self, case_documents: list[dict]) -> dict:

        describer = DocumentDescriber(
            llm=self.llm,
            actions=[],
            prompt=self.poclaims_conflicts_prompt,
        )
        case_documents_md = convert_documents_ids_to_markdown(case_documents)
        result = await describer.describe(case_documents_md)
        print("---conflicts---")
        print(result)
        print("---")
        return result

    async def _missing_documents(self, case_documents: list[dict]) -> dict:

        describer = DocumentDescriber(
            llm=self.llm,
            actions=[],
            prompt=self.missing_docs_prompt,
        )
        case_documents_md = convert_documents_ids_to_markdown(case_documents)
        result = await describer.describe(case_documents_md)
        print("---missing====")
        print(result)
        print("---")
        return result

    async def _extract_json(
        self, case_summary: str, description_data: dict, classification_data: dict
    ) -> dict:
        extractor = JSONExtractor(
            llm=self.llm,
            actions=self.extractor_actions,
            prompt=self.extractor_prompt,
            json_structure=self.json_structure,
        )
        file_id = description_data.get("file_id")
        document = description_data.get("document")
        doc_description = description_data.get("description")
        doc_classification = classification_data.get(file_id)

        if not document or not doc_description:
            return {
                **description_data,
                "json": None,
                "error": description_data.get("error", "Missing data"),
            }

        json_data = await extractor.extract(
            document, case_summary, doc_description, doc_classification
        )
        return {
            **description_data,
            **{"classification": doc_classification},
            "json": json_data,
        }

    async def process_documents(self, file_paths: list[str]) -> list[dict]:
        # # Step 1: Read all documents
        read_tasks = [self._read_document(fp) for fp in file_paths]
        file_contents = await asyncio.gather(*read_tasks)
        print("Process started ... ")
        # Step 2: Describe all documents
        print("Description started ... ")
        describe_tasks = [self._describe_document(doc) for doc in file_contents]
        description_results = await asyncio.gather(*describe_tasks)
        print("Classification started ... ")
        # Step 3: Classify documents
        classification_result = await self._classify_document(description_results)
        case_summary = classification_result.get("case_summary")
        docs_classification = classification_result.get("document_labels")

        print("JSON Generation started ... ")
        # Step 4: Extract JSON
        extract_tasks = [
            self._extract_json(
                case_summary=case_summary,
                classification_data=docs_classification,
                description_data=desc,
            )
            for desc in description_results
        ]
        final_results = await asyncio.gather(*extract_tasks)

        print("MD started ... ")
        # Step 5: Convert to markdown
        md_results = convert_to_markdown(final_results)

        print("Combination started ... ")
        # Step 6: Combine results
        combiner = JSONCombiner(
            llm=self.llm,
            actions=[],
            prompt=self.combiner_prompt,
            json_structure=self.json_structure,
        )
        combined_results = await combiner.combine(case_summary, md_results)

        print("Missing Keys started ... ")
        # Step 7: Revise for Missing Keys
        missing_keys = find_missing_keys(
            schema=self.json_structure, data=combined_results
        )

        print(f"{missing_keys=}")

        print("MD 2 started ... ")
        md_results_wojson = convert_to_markdown(final_results, include_json=False)

        print("Revisor started ... ")
        revisor = Revisor(llm=self.llm, actions=[], prompt=self.revisor_prompt)

        filled_dict = await revisor.revise(
            document=md_results_wojson, missing_keys=str(missing_keys)
        )
        print("Injection started ... ")
        print(f"{filled_dict=}")
        print("ON ... ")
        print(f"{combined_results=}")
        revised_results = inject_flattened_values(filled_dict, combined_results)

        return revised_results
