from app.models.schemas import TestCaseType


SYSTEM_PROMPT = """You are a senior QA engineer with deep expertise in software testing.
Your task is to generate structured test cases in valid JSON format.
Always respond with ONLY a JSON array — no markdown fences, no explanation text.
Every test case must follow the exact schema provided in the user prompt."""


def _base_schema_description() -> str:
    return """
Each test case object in the array must have exactly these fields:
{
  "title": "short descriptive title",
  "priority": "high" | "medium" | "low",
  "preconditions": ["list of setup conditions"],
  "steps": [
    {"step_number": 1, "action": "what tester does", "expected_result": "what should happen"}
  ],
  "expected_outcome": "overall pass condition",
  "tags": ["relevant", "tags"]
}
"""


def build_positive_prompt(
    ui_description: str,
    requirements: str,
    max_cases: int
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for positive test cases.
    Positive = valid inputs, happy path, all requirements met.
    """
    user_prompt = f"""
Generate exactly {max_cases} POSITIVE test cases for the following:

UI Description:
{ui_description}

Product Requirements:
{requirements}

Positive test cases must:
- Cover the main happy-path flows
- Use valid inputs that satisfy all requirements
- Verify that each functional requirement is fulfilled
- Include boundary values that should PASS (e.g., minimum valid password length)

{_base_schema_description()}

Respond with ONLY a JSON array of {max_cases} test case objects.
"""
    return SYSTEM_PROMPT, user_prompt.strip()


def build_negative_prompt(
    ui_description: str,
    requirements: str,
    max_cases: int
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for negative test cases.
    Negative = invalid inputs, error handling, rejection flows.
    """
    user_prompt = f"""
Generate exactly {max_cases} NEGATIVE test cases for the following:

UI Description:
{ui_description}

Product Requirements:
{requirements}

Negative test cases must:
- Use invalid, missing, or malformed inputs
- Test error messages and validation feedback shown to the user
- Test rejection flows (e.g., wrong password, expired session)
- Verify the system does NOT allow invalid operations
- Cover each field's validation rules

{_base_schema_description()}

Respond with ONLY a JSON array of {max_cases} test case objects.
"""
    return SYSTEM_PROMPT, user_prompt.strip()


def build_edge_case_prompt(
    ui_description: str,
    requirements: str,
    max_cases: int
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for edge/boundary test cases.
    Edge = extreme inputs, race conditions, unusual but valid states.
    """
    user_prompt = f"""
Generate exactly {max_cases} EDGE CASE test cases for the following:

UI Description:
{ui_description}

Product Requirements:
{requirements}

Edge case test cases must:
- Test exact boundary values (min-1, min, max, max+1)
- Test special characters, unicode, very long strings, empty strings
- Test concurrent or rapid repeated actions (e.g. double-submit)
- Test unusual but technically valid inputs (e.g. leading/trailing whitespace)
- Test system behaviour under unexpected conditions

{_base_schema_description()}

Respond with ONLY a JSON array of {max_cases} test case objects.
"""
    return SYSTEM_PROMPT, user_prompt.strip()


# Dispatch map — maps TestCaseType → prompt builder function
PROMPT_BUILDERS = {
    TestCaseType.POSITIVE:   build_positive_prompt,
    TestCaseType.NEGATIVE:   build_negative_prompt,
    TestCaseType.EDGE_CASE:  build_edge_case_prompt,
}