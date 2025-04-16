from typing import Dict, List
from loguru import logger
from langgraph.prebuilt import create_react_agent
from langchain_core.output_parsers import JsonOutputParser

from general_inference import BaseLLM
from templates.schemas import CaseAnalysis, RevisorSchema
from templates.claim_json_schema import ClaimForm
from templates.employment_json_schema import EmployeeForm
from utils.helpers import clean_json_string


class BaseAgentRunner:
    def __init__(self, llm, actions=None, prompt=""):
        self.llm = llm
        self.actions = actions or []
        self.prompt = prompt
        self.agent = create_react_agent(self.llm, self.actions, prompt=self.prompt)

    async def run(self, messages: list[dict]):
        agent_input = {"messages": messages}
        response = await self.agent.ainvoke(agent_input)
        return response["messages"][-1].content


class DocumentDescriber(BaseLLM):
    def __init__(self, llm, prompt):
        super().__init__(model=llm, template=prompt, keys=["document"])

    async def describe(self, document: str) -> str:
        content = await self.get_chat_response_regular({"document": document})
        return content


class DocumentClassifier(BaseLLM):
    def __init__(self, llm, prompt):
        super().__init__(
            model=llm,
            template=prompt,
            keys=["documents_description"],
            parser=JsonOutputParser(pydantic_object=CaseAnalysis),
        )

    async def classify(self, user_claim: str, docs_desc_md: str) -> Dict:
        content = await self.get_chat_response_regular(
            {
                "user_claim": user_claim,
                "documents_description": docs_desc_md,
                "output_schema": CaseAnalysis.Config.json_schema_extra["example"],
            }
        )
        return content


class JSONExtractor(BaseLLM):
    def __init__(self, llm, prompt, json_structure):

        self.parser = (
            JsonOutputParser(pydantic_object=ClaimForm)
            if "parties" in json_structure
            else JsonOutputParser(pydantic_object=EmployeeForm)
        )
        self.output_schema = (
            ClaimForm.Config.json_schema_extra["example"]
            if "parties" in json_structure
            else EmployeeForm.Config.json_schema_extra["example"]
        )
        super().__init__(
            model=llm,
            template=prompt,
            keys=["document"],
            parser=self.parser,
        )

    async def extract(
        self,
        case_summary: str,
        classification: str,
        user_claim: str,
        document: str,
        description: str,
    ) -> dict:
        content = await self.get_chat_response_regular(
            dict(
                case_summary=case_summary,
                classification=classification,
                user_claim=user_claim,
                document_description=description,
                output_schema=self.output_schema,
                document=document,
            )
        )
        return content


class JSONCombiner(BaseLLM):
    def __init__(self, llm, prompt, json_structure):
        self.parser = (
            JsonOutputParser(pydantic_object=ClaimForm)
            if "parties" in json_structure
            else JsonOutputParser(pydantic_object=EmployeeForm)
        )
        self.output_schema = (
            ClaimForm.Config.json_schema_extra["example"]
            if "parties" in json_structure
            else EmployeeForm.Config.json_schema_extra["example"]
        )
        super().__init__(
            llm, template=prompt, keys=["documents_descriptions_md"], parser=self.parser
        )

    async def combine(self, case_summary: str, documents_descriptions_md: str) -> dict:
        content = await self.get_chat_response_regular(
            dict(
                case_summary=case_summary,
                documents_descriptions_md=documents_descriptions_md,
                output_schema=self.output_schema,
            )
        )
        return content


class Revisor(BaseLLM):
    def __init__(self, llm, prompt):
        self.original_prompt = prompt
        super().__init__(
            model=llm,
            template=prompt,
            keys=["document"],
            parser=JsonOutputParser(pydantic_object=RevisorSchema),
        )

    async def revise(self, document: str, missing_keys: str) -> str:

        content = await self.get_chat_response_regular(
            dict(
                missing_keys=missing_keys,
                document=document,
                output_schema=RevisorSchema.Config.json_schema_extra["example"],
            )
        )
        return content


class Summarizer(BaseLLM):
    def __init__(self, llm, prompt):
        self.original_prompt = prompt
        super().__init__(
            model=llm,
            template=prompt,
            keys=["conversation"],
        )

    async def summarize(self, case_summary: str, history: List[Dict]) -> str:

        content = await self.get_chat_response_regular(
            dict(
                case_summary=case_summary,
                conversation=history,
            )
        )
        return content


class ReConstructor(BaseAgentRunner):
    def __init__(self, llm, actions, prompt):
        self.original_prompt = prompt
        super().__init__(llm, actions=actions, prompt=prompt)

    async def reconstruct(
        self, user_response: str, missing_keys: List, all_keys: List
    ) -> Dict:
        try:
            self.prompt = self.original_prompt.format(
                missing_keys=missing_keys, all_keys=all_keys
            )
            print("RECONSTRCUTOR PROMPT")
            print(self.prompt)
            print("RECONSTRCUTOR PROMPT")
            self.agent = create_react_agent(self.llm, self.actions, prompt=self.prompt)
            content = await self.run([{"role": "user", "content": user_response}])
            content = clean_json_string(content)
            return await JsonOutputParser().ainvoke(content)
        except Exception as ex:
            logger.info(f"Exception in Reconstructor: {ex}")
            return content


class Officer(BaseAgentRunner):
    def __init__(self, llm, actions, prompt):
        super().__init__(llm, actions=actions, prompt=prompt)

    async def serve(self, messages: List[Dict]) -> str:
        return await self.run(messages)


# General Detector Agent
class Generator(BaseAgentRunner):
    def __init__(self, llm, actions, prompt):
        self.original_prompt = prompt
        super().__init__(llm, actions=actions, prompt=prompt)

    async def generate(self, user_claims, document_descriptions: List[str]) -> str:
        self.prompt = self.original_prompt.format(
            document_descriptions=document_descriptions
        )
        self.agent = create_react_agent(self.llm, self.actions, prompt=self.prompt)
        content = await self.run([{"role": "user", "content": user_claims}])
        return content


class ClaimantEvaluator(BaseAgentRunner):
    def __init__(self, llm, actions, prompt):
        self.original_prompt = prompt
        super().__init__(llm, actions=actions, prompt=prompt)

    async def evaluate(self, claim_value: str, user_details: str) -> Dict:
        self.prompt = self.original_prompt.format(claim_value=claim_value)
        self.agent = create_react_agent(self.llm, self.actions, prompt=self.prompt)
        content = await self.run([{"role": "user", "content": user_details}])
        content = clean_json_string(content)
        return content
