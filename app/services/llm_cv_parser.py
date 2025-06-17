import json
from docx import Document as DocxDocument
from app.utils.audit_logger import logger
from app.utils.llm_utils import query_openai

# — your full prompt, with a single placeholder —
PROMPT_TEMPLATE = """
You are an experienced expert parser.

Carefully read the CV content provided below. Extract the following fields into structured JSON.
Be precise and resilient: the CV may contain spelling mistakes, inconsistent or unusual formatting, 
inconsistent or missing sections or partial information.
Use inference where needed (e.g. identifying likely links or field names even if spelled incorrectly or dates that contain typos
 - infer the most likely correct date).
Normalize your return variables (e.g. M.Sc. → MSc, Ph.D → PhD).

There might be private_milestones like childhood experiences, marriage, child birth or similar. Put this into the private_milestones section.
Please do distinguish between "personal_achievements" in a professional sense and "private_milestones" in a private context
and sort the information correspondingly.

Return:
- full_name
- email
- phone
- linkedin
- github
- website
- education: list of {{degree, field, start_date, end_date, institution}}
- professional_experience: list of {{title, company, start_date, end_date, location, role_type, role_description}}
- languages: list of {{language, proficiency_written, proficiency_spoken}}
- further_education: list of {{title, start_date, end_date, institution}}
- certifications: list of {{name, issuer, start_date, end_date}}
- awards: list of {{name, awarded_by, start_date, end_date}}
- publications: list of {{start_date, end_date, title, journal, authors}}
- personal_achievements: list of {{start_date, end_date, achievement, description}}
- private_milestones: list of {{start_date, end_date, event, description}}

Also return a "short_bio" summarizing the person in 2–3 sentences.

Here is the CV:

{full_text}
"""

def extract_text_from_docx(path: str) -> str:
    """Load a .docx and return its non-empty paragraphs joined by newlines."""
    doc = DocxDocument(path)
    return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())

def parse_cv_with_llm(docx_path: str) -> tuple[dict, str, str]:
    """
    Returns:
      - parsed_data: the JSON→dict from the LLM
      - prompt_sent: the actual prompt string we sent
      - raw_response: the LLM’s raw JSON string
    """
    full_text = extract_text_from_docx(docx_path)
    prompt = PROMPT_TEMPLATE.format(full_text=full_text)
    logger.info("🔄 Querying OpenAI for CV parsing…")
    raw_response = query_openai(prompt)
    parsed_data = json.loads(raw_response)
    return parsed_data, prompt, raw_response
