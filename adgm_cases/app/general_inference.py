from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from typing import Any, List, Optional


class BaseLLM:
    """
    A base model class for handling prompt templates, parsers, and chain initialization.
    """

    def __init__(
        self,
        model: Optional[ChatOpenAI],
        template: str,
        keys: List[str] = [],
        parser: Optional[Any] = StrOutputParser(),
    ):
        """
        Initializes the base model with a template, parser, and model.

        Args:
            template (str): The prompt template to use.
            parser (Optional[Any]): The output parser for the model. Defaults to StrOutputParser.
            model (Optional[str]): The model name. Defaults to a GPT-4-lite model.
        """
        self.template = template
        self.parser = parser
        self.model = model
        self.keys = keys
        self.chain = None

    async def initialize_chain(self) -> None:
        """
        Initializes the chain using the provided template, parser, and model.
        """
        if not self.chain:
            # Dynamically build the message sequence
            messages = [SystemMessagePromptTemplate.from_template(self.template)]

            # Add human messages based on the keys in the template
            # This assumes the template has keys like {topic}, {context}, etc.
            for key in self.keys:
                messages.append(
                    HumanMessagePromptTemplate.from_template("{" + key + "}")
                )

            prompt = ChatPromptTemplate.from_messages(messages)
            self.chain = prompt | self.model | self.parser

    async def get_chat_response_regular(self, input_data: dict) -> Any:
        """
        Processes the input data through the initialized chain and returns the response.

        Args:
            input_data (dict): The input data for the model.

        Returns:
            Any: The AI model's response.
        """
        if not self.chain:
            await self.initialize_chain()
        return await self.chain.ainvoke(input_data)


class General(BaseLLM):
    """
    A specialized model for intent recognition using JSON parsing.
    """

    def __init__(self, template, parser):
        super().__init__(template=template, parser=parser)
