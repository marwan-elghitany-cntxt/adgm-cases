import asyncio
from typing import Dict, List
from langchain_core.output_parsers import JsonOutputParser
from agents import (
    DocumentClassifier,
    DocumentDescriber,
    Generator,
    JSONCombiner,
    JSONExtractor,
    Revisor,
)
from utils.helpers import (
    convert_documents_ids_to_markdown,
    convert_to_markdown,
    find_missing_keys,
    fix_claim_value,
    gen_file_id,
    inject_flattened_values,
    read_pdf_text,
    safely_fix_claim_value,
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
        missing_docs_prompt,
        not_refrenced_docs_prompt,
        poclaims_conflicts_prompt,
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
        self.missing_docs_prompt = missing_docs_prompt
        self.not_refrenced_docs_prompt = not_refrenced_docs_prompt
        self.poclaims_conflicts_prompt = poclaims_conflicts_prompt

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

    async def _classify_document(
        self, user_claim: str, case_documents: list[dict]
    ) -> dict:

        classifier = DocumentClassifier(
            llm=self.llm,
            actions=[],
            prompt=self.classifier_prompt,
        )
        case_documents_md = convert_documents_ids_to_markdown(case_documents)
        classification = await classifier.classify(user_claim, case_documents_md)
        print("---")
        print(classification)
        print("---")
        return await JsonOutputParser().ainvoke(classification)

    async def _extract_json(
        self,
        user_claim: str,
        case_summary: str,
        description_data: dict,
        classification_data: dict,
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
        doc_classification = next(
            (
                f"{entry['label']}** Since: {entry['reason']}"
                for entry in classification_data
                if entry["document_id"] == file_id
            ),
            None,
        )

        if not document or not doc_description:
            return {
                **description_data,
                "json": None,
                "error": description_data.get("error", "Missing data"),
            }

        json_data = await extractor.extract(
            user_claim, document, case_summary, doc_description, doc_classification
        )
        return {
            **description_data,
            **{"classification": doc_classification},
            "json": json_data,
        }

    async def run_all_detectors(
        self,
        user_claim: str,
        description_results: List[Dict],
        classification_result: Dict,
    ) -> tuple:
        """
        Runs all document-related detectors concurrently and returns their results.

        Returns:
            (missing_pts, conflict_pts)
        """
        # Map classification data by document_id
        classification_map = {
            item["document_id"]: {"label": item["label"], "reason": item["reason"]}
            for item in classification_result.get("details", [])
        }

        # Combine classification info into document descriptions
        enriched_descriptions = []
        for d in description_results:
            file_id = d.get("file_id")
            base_description = d.get("description", "-")
            classification_info = classification_map.get(file_id, {})

            # Append label/reason if they exist
            label = classification_info.get("label")
            reason = classification_info.get("reason")

            enriched_description = base_description
            if label or reason:
                enriched_description += (
                    f"\n\nLabel: {label or ''}\nReason: {reason or ''}"
                )

            enriched_descriptions.append(enriched_description)

        # Prompts for the detectors
        prompts = [
            (self.missing_docs_prompt, "missing"),
            # (self.not_refrenced_docs_prompt, "not_referenced"),
            (self.poclaims_conflicts_prompt, "conflict"),
        ]

        detectors = {
            label: Generator(llm=self.llm, actions=[], prompt=prompt)
            for prompt, label in prompts
        }

        # Run all prompts concurrently
        results = await asyncio.gather(
            *[
                detector.generate(
                    user_claims=user_claim, document_descriptions=enriched_descriptions
                )
                for detector in detectors.values()
            ]
        )

        return tuple(results)

    async def process_documents(self, file_paths: list[str]) -> list[dict]:
        user_claim_desc = ""
        # # Step 1: Read all documents
        read_tasks = [self._read_document(fp) for fp in file_paths]
        file_contents = await asyncio.gather(*read_tasks)
        print("Process started ... ")
        # Step 2: Describe all documents
        print("Description started ... ")
        describe_tasks = [self._describe_document(doc) for doc in file_contents]
        description_results = await asyncio.gather(*describe_tasks)
        for i, description in enumerate(description_results):
            if "claims_text.txt" in description["file"]:
                # user_claim_file_id = description["file_id"]
                # user_claim = description["document"]
                user_claim_desc = description["description"]
                del description_results[i]

        # Step 3: Classify documents
        print("Classification started ... ")
        classification_result = await self._classify_document(
            user_claim=user_claim_desc, case_documents=description_results
        )
        case_summary = classification_result.get("case_summary")
        docs_classification = classification_result.get("details")

        print("Detectors started ... ")
        results = await self.run_all_detectors(
            user_claim=user_claim_desc,
            description_results=description_results,
            classification_result=classification_result,
        )
        missing_pts, cfl_pts = results

        print("")
        print(f"{missing_pts=}")
        print("")
        print("")
        print(f"{cfl_pts=}")
        print("")

        print("JSON Generation started ... ")
        # Step 4: Extract JSON
        extract_tasks = [
            self._extract_json(
                user_claim=user_claim_desc,
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

        print("<<md_results>>")
        print(md_results)
        print("<<md_results>>")

        print("Combination started ... ")
        # Step 6: Combine results
        combiner = JSONCombiner(
            llm=self.llm,
            actions=[],
            prompt=self.combiner_prompt,
            json_structure=self.json_structure,
        )
        combined_results = await combiner.combine(case_summary, md_results)

        print("<<combined_results>>")
        print(combined_results)
        print("<<combined_results>>")

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
        
        revised_results = safely_fix_claim_value(revised_results)

        return revised_results, missing_pts, cfl_pts
