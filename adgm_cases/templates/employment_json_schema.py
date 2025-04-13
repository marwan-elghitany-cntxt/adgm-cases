from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class AdditionalParty(BaseModel):
    full_name: str = Field(..., description="Full name of the additional party")


class Party(BaseModel):
    full_name: str = Field(..., description="Full name of the main party")
    additional_claimants: Optional[List[AdditionalParty]] = Field(default_factory=list)
    additional_defendants: Optional[List[AdditionalParty]] = Field(default_factory=list)


class SelfRepresentedDetails(BaseModel):
    address_for_service: str
    telephone: str
    email: str
    name_of_authorised_officer: str
    capacity_to_act_for_claimant: str


class LegalRepresentativeDetails(BaseModel):
    legal_representative: str
    firm: str
    address_for_service: str
    firm_reference: str
    contact_name: str
    contact_telephone: str
    contact_email: str


class ClaimantLegalDetails(BaseModel):
    self_represented_or_authorised_officer: SelfRepresentedDetails
    legal_represented_filled_by_laywer: LegalRepresentativeDetails


class DefendantLegalDetails(BaseModel):
    home_or_work_address: str
    contact_email: str
    contact_telephone: str


class LegalRepresentation(BaseModel):
    claimant_details: ClaimantLegalDetails
    defendant_details: DefendantLegalDetails


class ParticularsOfClaim(BaseModel):
    details: List[str]
    supporting_documents: List[str]


class ClaimDetails(BaseModel):
    nature_of_claim: str  # You can use Literal[...] for fixed values if needed
    claim_value: str
    interest_details: str
    final_orders_sought: List[str]
    particulars_of_claim: ParticularsOfClaim


class EmploymentTerms(BaseModel):
    employment_agreement_attached: bool
    rate_of_remuneration: str


class Jurisdiction(BaseModel):
    grounds_for_claim: str  # Literal[...] also applicable here


class Mediation(BaseModel):
    preferred: str
    reason_if_no: str


class EmployeeForm(BaseModel):
    claimant: Party
    defendant: Party
    legal_representation: LegalRepresentation
    claim_details: ClaimDetails
    employment_terms: EmploymentTerms
    jurisdiction: Jurisdiction
    mediation: Mediation

    class Config:
        json_schema_extra = {
            "example": {
                "claimant": {
                    "full_name": "<FULL_CLAIMANT>",
                    "additional_claimants": [
                        {"full_name": "<ADDITIONAL_CLAIMANT_FULL_NAME_IF_MORE_THAN_2>"}
                    ],
                },
                "defendant": {
                    "full_name": "<FULL_DEFENDANT_NAME>",
                    "additional_defendants": [
                        {"full_name": "<ADDITIONAL_DEFENDANT_FULL_NAME_IF_MORE_THAN_2>"}
                    ],
                },
                "legal_representation": {
                    "claimant_details": {
                        "self_represented_or_authorised_officer": {
                            "address_for_service": "<extracted_claimant_address_for_service>",
                            "telephone": "<extracted_claimant_telephone>",
                            "email": "<extracted_claimant_email_address>",
                            "name_of_authorised_officer": "<extracted_name_of_authorised_officer>",
                            "capacity_to_act_for_claimant": "<extracted_capacity_to_act>",
                        },
                        "legal_represented_filled_by_laywer": {
                            "legal_representative": "<extracted_laywer_full_name>",
                            "firm": "<extracted_lawyer_firm_name>",
                            "address_for_service": "<extracted__lawyer_address_for_service>",
                            "firm_reference": "<extracted_lawyer_firm_reference_number>",
                            "contact_name": "<extracted_contact_name_or_laywer_name>",
                            "contact_telephone": "<extracted_lawyer_phone>",
                            "contact_email": "<extracted_lawyer_email>",
                        },
                    },
                    "defendant_details": {
                        "home_or_work_address": "<extracted_defendant_address>",
                        "contact_email": "<extracted_defendant_contact_email>",
                        "contact_telephone": "<extracted_defendant_contact_phone>",
                    },
                },
                "claim_details": {
                    "nature_of_claim": "<Health and Safety>",
                    "claim_value": "<10000 AED>",
                    "interest_details": "<Rate of the Interest % >",
                    "final_orders_sought": [
                        "<extracted_order_1>",
                        "<extracted_order_2>",
                    ],
                    "particulars_of_claim": {
                        "details": [
                            "<PARTICULAR_OF_CLAIM_DETAIL_1>",
                            "<PARTICULAR_OF_CLAIM_DETAIL_2>",
                        ],
                        "supporting_documents": [
                            "<SUPPORTING_DOCUMENT_1>",
                            "<SUPPORTING_DOCUMENT_2>",
                        ],
                    },
                },
                "employment_terms": {
                    "employment_agreement_attached": True,
                    "rate_of_remuneration": "<salary>",
                },
                "jurisdiction": {
                    "grounds_for_claim": "<The claim relates to an ADGM entity>"
                },
                "mediation": {
                    "preferred": "<extracted_or_user_input_mediation_choice>",
                    "reason_if_no": "<user_input_if_required>",
                },
            }
        }
