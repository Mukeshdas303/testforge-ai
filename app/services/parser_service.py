import json
import re
import logging
from app.models.schemas import TestCase, TestStep, TestCaseType, TestCasePriority

logger = logging.getLogger(__name__)


class TestCaseParser:
    """
    Converts raw LLM string output → list[TestCase].

    phi3 occasionally wraps JSON in markdown fences or adds
    leading commentary. This parser strips all of that.
    """

    def _clean_llm_output(self, raw: str) -> str:
        """Remove markdown fences, leading/trailing text, keep only JSON array."""
        # Strip ```json ... ``` or ``` ... ``` fences
        raw = re.sub(r"```(?:json)?", "", raw)
        raw = raw.strip("`").strip()

        # Find the first '[' and last ']' — extract the JSON array
        start = raw.find("[")
        end   = raw.rfind("]")
        if start == -1 or end == -1:
            raise ValueError(f"No JSON array found in LLM output. Raw:\n{raw[:300]}")

        return raw[start:end + 1]

    def _parse_step(self, raw_step: dict, idx: int) -> TestStep:
        return TestStep(
            step_number    = raw_step.get("step_number", idx + 1),
            action         = str(raw_step.get("action", "")),
            expected_result= str(raw_step.get("expected_result", ""))
        )

    def _parse_priority(self, value: str) -> TestCasePriority:
        mapping = {
            "high":   TestCasePriority.HIGH,
            "medium": TestCasePriority.MEDIUM,
            "low":    TestCasePriority.LOW,
        }
        return mapping.get(str(value).lower(), TestCasePriority.MEDIUM)

    def _parse_single(self, raw: dict, case_type: TestCaseType) -> TestCase:
        steps = [
            self._parse_step(s, i)
            for i, s in enumerate(raw.get("steps", []))
            if isinstance(s, dict)
        ]

        return TestCase(
            title            = str(raw.get("title", "Untitled test case")),
            type             = case_type,
            priority         = self._parse_priority(raw.get("priority", "medium")),
            preconditions    = [str(p) for p in raw.get("preconditions", [])],
            steps            = steps,
            expected_outcome = str(raw.get("expected_outcome", "")),
            tags             = [str(t) for t in raw.get("tags", [])]
        )

    def parse(self, llm_output: str, case_type: TestCaseType) -> list[TestCase]:
        """
        Parse raw LLM text into a list of TestCase objects.
        Returns an empty list (not exception) on total parse failure
        so one bad response doesn't abort the whole generation run.
        """
        try:
            cleaned = self._clean_llm_output(llm_output)
            raw_list = json.loads(cleaned)

            if not isinstance(raw_list, list):
                logger.warning("LLM returned JSON but not an array — wrapping")
                raw_list = [raw_list]

            results = []
            for item in raw_list:
                if isinstance(item, dict):
                    try:
                        results.append(self._parse_single(item, case_type))
                    except Exception as e:
                        logger.warning(f"Skipping malformed test case: {e}")

            return results

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Parser failed for {case_type}: {e}")
            return []


parser_service = TestCaseParser()