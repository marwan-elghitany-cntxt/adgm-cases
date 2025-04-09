from typing import Dict, List
from langgraph.prebuilt import create_react_agent
from langchain_core.output_parsers import JsonOutputParser

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


class DocumentDescriber(BaseAgentRunner):
    def __init__(self, llm, actions, prompt):
        super().__init__(llm, actions=actions, prompt=prompt)

    async def describe(self, document: str) -> str:
        content = await self.run([{"role": "user", "content": document}])
        return content


class DocumentClassifier(BaseAgentRunner):
    def __init__(self, llm, actions, prompt):
        self.original_prompt = prompt
        super().__init__(llm, actions=actions, prompt=prompt)

    async def classify(self, user_claim: str, docs_desc_md: str) -> Dict:

        self.prompt = self.original_prompt.format(user_claim=user_claim)
        self.agent = create_react_agent(self.llm, self.actions, prompt=self.prompt)
        content = await self.run([{"role": "user", "content": docs_desc_md}])
        content = clean_json_string(content)
        return content


class JSONExtractor(BaseAgentRunner):
    def __init__(self, llm, actions, prompt, json_structure):
        self.json_structure = json_structure
        self.original_prompt = prompt
        super().__init__(llm, actions=actions, prompt=prompt)

    async def extract(
        self,
        user_claim: str,
        document: str,
        case_summary: str,
        description: str,
        classification: str,
    ) -> dict:
        self.prompt = self.original_prompt.format(
            user_claim=user_claim,
            case_summary=case_summary,
            document_description=description,
            classification=classification,
        )
        self.agent = create_react_agent(self.llm, self.actions, prompt=self.prompt)
        messages = [
            {"role": "system", "content": str(self.json_structure)},
            {"role": "user", "content": document},
        ]
        content = await self.run(messages)
        return content


class JSONCombiner(BaseAgentRunner):
    def __init__(self, llm, actions, prompt, json_structure):
        self.json_structure = json_structure
        self.original_prompt = prompt
        super().__init__(llm, actions=actions, prompt=prompt)

    async def combine(self, case_summary: str, output_results: str) -> dict:
        self.prompt = self.original_prompt.format(case_summary=case_summary)
        self.agent = create_react_agent(self.llm, self.actions, prompt=self.prompt)

        messages = [
            {
                "role": "system",
                "content": f"Output Schema Format: {str(self.json_structure)}",
            },
            {"role": "user", "content": output_results},
        ]
        content = await self.run(messages)
        content = clean_json_string(content)
        return await JsonOutputParser().ainvoke(content)


class Revisor(BaseAgentRunner):
    def __init__(self, llm, actions, prompt):
        self.original_prompt = prompt
        super().__init__(llm, actions=actions, prompt=prompt)

    async def revise(self, document: str, missing_keys: str) -> str:

        self.prompt = self.original_prompt.format(
            case_document=document,
        )
        self.agent = create_react_agent(self.llm, self.actions, prompt=self.prompt)
        content = await self.run([{"role": "user", "content": str(missing_keys)}])
        content = clean_json_string(content)
        return await JsonOutputParser().ainvoke(content)


class ReConstructor(BaseAgentRunner):
    def __init__(self, llm, actions, prompt):
        self.original_prompt = prompt
        super().__init__(llm, actions=actions, prompt=prompt)

    async def reconstruct(self, user_response: str, missing_keys: str) -> Dict:

        self.prompt = self.original_prompt.format(missing_keys=missing_keys)
        self.agent = create_react_agent(self.llm, self.actions, prompt=self.prompt)
        content = await self.run([{"role": "user", "content": user_response}])
        content = clean_json_string(content)
        return await JsonOutputParser().ainvoke(content)


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
