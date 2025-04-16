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

CACHED_VALUES = {
    "particular_of_claims": "immarwanelghitanyandiworkedaschieffinancialofficeratcntxtfzcoindubaiearningasalaryof33000aedpermonthfromthestartmysalarywasoftendelayedanddespitepromisesthingsdidntimproveialsocoveredairticketsformyfamilyandsometransportcostswhichwereneverreimbursedfrommaytodecember2023iwasntpaidatallsoiresignedindecemberevenaftermyresignationwasacknowledgedihaventreceivedmypendingsalaryendofservicebenefitsnoticepayorreimbursementsintotalimowedaed30717485andimseekingthecourtshelptorecoverthisamountwithinterestandlegalcosts1outstandingsalaryapril2023partialmaydec2023277990002endofservicebenefitsbasedon1year11months18days23376163paymentinlieuof3monthnoticeperiod99000004airticketallowancefortheyear20226587005reimbursementoftaxifare22169total30717485",
    "file_names": [
        "personal_ADGM - Resignation Email - CFI3.pdf",
        "Marwan Elghitany - Chief Financial Officer Offer Letter.pdf",
    ],
    "respond": """### Conflicts & Highlights Detected:
- Claim Amount Discrepancy: The total claim amount stated is 307,174.85 AED, but based on the breakdown provided, it should be 407,174.85 AED. There's a difference of 100,000.00 AED.
- Unpaid Salaries: The claim includes unpaid salary for December 2023, but supporting documents only cover up to November 2023.
- Payment in Lieu of Notice Period: A claim for 99,000.00 AED is included, but not supported by documents.
- Air Ticket Allowance: A claim for 6,587.00 AED for 2022 is included, but not supported by documents.
- Reimbursement of Taxi Fare: A claim for 221.69 AED is included, but not supported by documents.
### Missing Information:
- Additional Claimants: Full names are required.
- Additional Defendants: Full names are required.
- Claimant's Legal Representation:
    - Address for service if self-represented or authorized officer.
    - Details of legal representative if represented by a lawyer, including firm, address, firm reference, contact name, telephone, and email.
- Defendant's Legal Representation: Contact email and telephone.
- Claim Details: Interest details and claim value.
- Mediation: Preference and reason if not preferred.
### Documents Required:
- Supporting Documents: For the claims of unpaid salary for December 2023, payment in lieu of notice period, air ticket allowance for 2022, and reimbursement of taxi fare.

Please provide the missing information and documents to proceed smoothly with your ADGM form submission. If you need further assistance, feel free to ask!""",
    "json_result": {
        "claimant": {
            "full_name": "Marwan Elghitany",
            "additional_claimants": [{"full_name": None}],
        },
        "defendant": {
            "full_name": "CNTXT FZCO",
            "additional_defendants": [{"full_name": None}],
        },
        "legal_representation": {
            "claimant_details": {
                "self_represented_or_authorised_officer": {
                    "address_for_service": None,
                    "telephone": "+971664588976",
                    "email": "marwan.elghitany@gmail.com",
                    "name_of_authorised_officer": "Marwan Elghitany",
                    "capacity_to_act_for_claimant": "Chief Financial Officer",
                },
                "legal_represented_filled_by_laywer": {
                    "legal_representative": None,
                    "firm": None,
                    "address_for_service": None,
                    "firm_reference": None,
                    "contact_name": None,
                    "contact_telephone": None,
                    "contact_email": None,
                },
            },
            "defendant_details": {
                "home_or_work_address": "Dubai, UAE",
                "contact_email": None,
                "contact_telephone": None,
            },
        },
        "claim_details": {
            "nature_of_claim": "Employment Law",
            "claim_value": "83641.892 USD (❌)",
            "interest_details": None,
            "final_orders_sought": [
                "Settlement of unpaid salaries",
                "Settlement of End of Service Gratuity",
            ],
            "particulars_of_claim": {
                "details": [
                    "Unpaid salaries from April 2023 to November 2023",
                    "Partial payment for April 2023",
                ],
                "supporting_documents": [
                    "Notice of Resignation",
                    "Employment Contract",
                ],
            },
        },
        "employment_terms": {
            "employment_agreement_attached": True,
            "rate_of_remuneration": "33,000 AED",
        },
        "jurisdiction": {"grounds_for_claim": "The claim relates to an ADGM entity"},
        "mediation": {"preferred": None, "reason_if_no": None},
    },
    "case_summary": """Marwan Elghitany, serving as the Chief Financial Officer at CNTXT FZCO in Dubai, has initiated legal proceedings to recover unpaid salary, end-of-service benefits, notice pay, and reimbursements totaling 307,174.85 AED. The claim includes outstanding salary from April 2023 to December 2023, end-of-service benefits calculated for a tenure of nearly two years, a three-month notice period payment, an air ticket allowance for 2022, and taxi fare reimbursement. The legal action is grounded in employment law, seeking court intervention to enforce payment along with interest and legal costs. The employment offer letter (Document 1) confirms Marwan's monthly salary package of 33,000 AED, including various allowances, and outlines a one-month termination notice post-probation. The resignation notice (Document 2) cites non-payment of salaries from January 2022 to November 2023 as a breach of ADGM Employment Regulations 2019, prompting immediate resignation and a request for settlement of dues.""",
    "missing_values": [
        "claimant.additional_claimants.full_name",
        "defendant.additional_defendants.full_name",
        "legal_representation.claimant_details.self_represented_or_authorised_officer.address_for_service",
        "legal_representation.claimant_details.legal_represented_filled_by_laywer.legal_representative",
        "legal_representation.claimant_details.legal_represented_filled_by_laywer.firm",
        "legal_representation.claimant_details.legal_represented_filled_by_laywer.address_for_service",
        "legal_representation.claimant_details.legal_represented_filled_by_laywer.firm_reference",
        "legal_representation.claimant_details.legal_represented_filled_by_laywer.contact_name",
        "legal_representation.claimant_details.legal_represented_filled_by_laywer.contact_telephone",
        "legal_representation.claimant_details.legal_represented_filled_by_laywer.contact_email",
        "legal_representation.defendant_details.contact_email",
        "legal_representation.defendant_details.contact_telephone",
        "claim_details.interest_details",
        "mediation.preferred",
        "mediation.reason_if_no",
        "claim_details.claim_value",
    ],
    "conflicts": """<conflict> Claim is incorrect. Claim 307,174.85 AED, but calculated 407,174.85 AED based on the breakdown. The difference is 100,000.00 AED </conflict>
<conflict>[CONFLICT_1_DETAILS: The user's summary claims an outstanding salary from April 2023 to December 2023, while the supporting document (Notice of Resignation) only mentions unpaid salaries from April 2023 to November 2023, with no mention of December 2023.]</conflict>  
<conflict>[CONFLICT_2_DETAILS: The user's summary includes a claim for a 3-month notice period payment of 99,000 AED, which is not mentioned in the supporting documents. The Offer Letter specifies a 1-month notice period post-probation, not 3 months.]</conflict>  
<conflict>[CONFLICT_3_DETAILS: The user's summary includes an air ticket allowance claim for the year 2022 amounting to 6,587.00 AED, which is not mentioned in any of the supporting documents.]</conflict>  
<conflict>[CONFLICT_4_DETAILS: The user's summary includes a reimbursement of taxi fare claim amounting to 221.69 AED, which is not mentioned in any of the supporting documents.]</conflict>""",
}
