from typing import List, Optional
from pydantic import BaseModel, Field


class Party(BaseModel):
    full_name: str
    address: str
    telephone: str
    email: str


class LegalRepresentative(BaseModel):
    name: str
    firm: str
    contact_person: str
    telephone: str
    email: str


class LegalRepresentation(BaseModel):
    type: str  # e.g. "Legal Representative", "Self-represented"
    legal_representative: LegalRepresentative


class ClaimDetails(BaseModel):
    nature_of_claim: str
    claim_value_usd: str
    interest_details: Optional[str]
    final_orders_sought: List[str]
    particulars_of_claim: str
    attached_documents: List[str]


class EmploymentTerms(BaseModel):
    employment_agreement_attached: bool
    rate_of_remuneration: str


class Parties(BaseModel):
    claimant: List[Party]
    defendant: List[Party]


class ClaimForm(BaseModel):
    parties: Parties
    legal_representation: LegalRepresentation
    claim_details: ClaimDetails
    employment_terms: EmploymentTerms

    class Config:
        json_schema_extra = {
            "example": {
                "parties": {
                    "claimant": [
                        {
                            "full_name": "<extracted_claimant_full_name>",
                            "address": "<extracted_claimant_address>",
                            "telephone": "<extracted_claimant_telephone_number>",
                            "email": "<extracted_claimant_email_address>",
                        }
                    ],
                    "defendant": [
                        {
                            "full_name": "<extracted_defendant_full_name>",
                            "address": "<extracted_defendant_address>",
                            "telephone": "<extracted_defendant_telephone_number>",
                            "email": "<extracted_defendant_email_address>",
                        }
                    ],
                },
                "legal_representation": {
                    "type": "<extracted_type_of_legal_representation>",
                    "legal_representative": {
                        "name": "<extracted_legal_representative_full_name>",
                        "firm": "<extracted_law_firm_name>",
                        "contact_person": "<extracted_contact_person_name>",
                        "telephone": "<extracted_legal_representative_telephone_number>",
                        "email": "<extracted_legal_representative_email_address>",
                    },
                },
                "claim_details": {
                    "nature_of_claim": "<extracted_nature_of_claim>",
                    "claim_value_usd": "<extracted_total_claim_value_in_usd>",
                    "interest_details": "<extracted_interest_rate_and_terms>",
                    "final_orders_sought": [
                        "<extracted_final_order_1_description>",
                        "<extracted_final_order_2_description>",
                    ],
                    "particulars_of_claim": "<extracted_particulars_of_claim_text>",
                    "attached_documents": [
                        "<attached_document_filename_or_id_1>",
                        "<attached_document_filename_or_id_2>",
                    ],
                },
                "employment_terms": {
                    "employment_agreement_attached": True,
                    "rate_of_remuneration": "<extracted_monthly_or_hourly_salary_amount>",
                },
            }
        }
