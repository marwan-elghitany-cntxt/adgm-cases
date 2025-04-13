from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict


class CaseDetail(BaseModel):
    document_id: str = Field(..., description="Unique identifier for the document")
    label: Literal["claimant", "defendant"] = Field(
        ..., description="Label assigned to the document"
    )
    reason: str = Field(
        ..., description="Explanation for why the document was assigned the given label"
    )


class CaseAnalysis(BaseModel):
    case_summary: str = Field(
        ...,
        description="A detailed coherent summary capturing the whole reasoning and context of the case with personal details",
    )
    details: List[CaseDetail] = Field(
        ..., description="List of labeled documents with reasoning"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "case_summary": "<A detailed coherent summary capturing the whole reasoning and context of the case with personal details>",
                "details": [
                    {
                        "document_id": "<document_id_1>",
                        "label": "claimant",
                        "reason": "<Explanation of why this document is labeled as claimant>",
                    },
                    {
                        "document_id": "<document_id_2>",
                        "label": "defendant",
                        "reason": "<Explanation of why this document is labeled as defendant>",
                    },
                ],
            }
        }


class RevisorSchema(BaseModel):

    class Config:
        json_schema_extra = {
            "example": {
                "<key1>": "<Extracted or inferred value for key1>",
                "<key2>": "<Extracted or inferred value for key2>",
                "<key3>": None,
            }
        }
