# Constants
# EMPLOYMENT_FORM_PATH = "/Users/marwan.elghitany/work/repos/adgm-cases/adgm_cases/forms/form_employment_v2.json"
# CLAIM_FORM_PATH = "/Users/marwan.elghitany/work/repos/my-notebooks/notebooks/research/adgm/forms/form_claim.json"
# EMPLOYMENT_FORM_PATH = "/workspaces/adgm-cases/adgm_cases/forms/form_employment.json"
# CLAIM_FORM_PATH = "/workspaces/adgm-cases/adgm_cases/forms/form_claim.json"
EMPLOYMENT_FORM = {
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
        "nature_of_claim": "ONE OF [<Breach of contract>, <Discrimination>, <Health and Safety>, <Hours of Work>, <Leave entitlements>, <Parental rights>, <Pay statements>, <Payment of wages>, <Termination of Employment]>",
        "claim_value": "<[claim_value] [currency]>",
        "interest_details": "<Rate of the Interest % >",
        "final_orders_sought": [
            "<extracted_order_1>",
            "<extracted_order_2>",
            "<extracted_order_3>",
        ],
        "particulars_of_claim": {
            "details": [
                "<PARTICULAR_OF_CLAIM_DETAIL_1>",
                "<PARTICULAR_OF_CLAIM_DETAIL_2>",
                "<PARTICULAR_OF_CLAIM_DETAIL_3>",
            ],
            "supporting_documents": [
                "<SUPPORTING_DOCUMENT_1>",
                "<SUPPORTING_DOCUMENT_2>",
                "<SUPPORTING_DOCUMENT_3>",
            ],
        },
    },
    "employment_terms": {
        "employment_agreement_attached": True,
        "rate_of_remuneration": "<salary>",
    },
    "jurisdiction": {
        "grounds_for_claim": "ONE OF [<The parties have agreed in writing to the jurisdiction of ADGM Courts>, <The claim relates to an ADGM entity>, <The claim relates to a contract or transaction in ADGM>, <The claim relates to an incident in ADGM>]"
    },
    "mediation": {
        "preferred": "<extracted_or_user_input_mediation_choice>",
        "reason_if_no": "<user_input_if_required>",
    },
}
CLAIM_FORM = {
    "parties": {
        "claimant": [
            {
                "full_name": "<extracted_claimant_name>",
                "address": "<extracted_claimant_address>",
                "telephone": "<extracted_claimant_phone>",
                "email": "<extracted_claimant_email>",
            }
        ],
        "defendant": [
            {
                "full_name": "<extracted_defendant_name>",
                "address": "<extracted_defendant_address>",
                "telephone": "<extracted_defendant_phone>",
                "email": "<extracted_defendant_email>",
            }
        ],
    },
    "legal_representation": {
        "type": "<extracted_representation_type>",
        "legal_representative": {
            "name": "<extracted_lawyer_name>",
            "firm": "<extracted_firm_name>",
            "contact_person": "<extracted_contact_person>",
            "telephone": "<extracted_contact_phone>",
            "email": "<extracted_contact_email>",
        },
    },
    "claim_details": {
        "nature_of_claim": "<extracted_claim_type>",
        "claim_value_usd": "<extracted_claim_value>",
        "interest_details": "<extracted_interest_details>",
        "final_orders_sought": ["<extracted_order_1>", "<extracted_order_2>"],
        "particulars_of_claim": "<extracted_particulars_text>",
        "attached_documents": ["<document_1>", "<document_2>"],
    },
    "employment_terms": {
        "employment_agreement_attached": True,
        "rate_of_remuneration": "<extracted_salary>",
    },
    "jurisdiction": {"grounds_for_claim": "<extracted_jurisdiction_basis>"},
    "mediation": {
        "preferred": "<extracted_or_user_input_mediation_choice>",
        "reason_if_no": "<user_input_if_required>",
    },
    "verification": {
        "litigant_type": "<litigant_in_person_or_legal_representative>",
        "certification_statement": "I certify that there are reasonable grounds for believing on the basis of provable facts and a reasonably arguable view of the law that the claim in these proceedings has reasonable prospects of success.",
        "signature_required": True,
    },
    "service_information": {
        "inside_uae": "<extracted_or_user_input_if_defendant_inside_uae>",
        "outside_uae": "<extracted_or_user_input_if_defendant_outside_uae>",
    },
    "response_guidelines": {
        "response_deadline": "14 days",
        "available_forms": {
            "defence": "CFI 8",
            "counterclaim": "CFI 9",
            "admission_with_time_request": "CFI 34",
            "jurisdiction_dispute": "CFI 12C",
        },
    },
}

TEMP_DIR = "users"
