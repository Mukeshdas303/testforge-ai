import json
import csv
import io
from datetime import datetime
from app.models.schemas import GenerationResult, ExportResponse


class ExportService:

    def _slugify(self, text: str) -> str:
        """Simple filename-safe slug."""
        return text[:30].lower().replace(" ", "_").replace("/", "-")

    # ── JSON export ────────────────────────────────────────────────────────────

    def to_json(self, result: GenerationResult) -> ExportResponse:
        payload = {
            "session_id":            result.session_id,
            "generated_at":          result.generated_at.isoformat(),
            "ui_description":        result.ui_description,
            "product_requirements":  result.product_requirements,
            "summary": {
                "total":      result.total_count,
                "positive":   result.positive_count,
                "negative":   result.negative_count,
                "edge_cases": result.edge_case_count,
            },
            "test_cases": [
                {
                    "id":               tc.id,
                    "title":            tc.title,
                    "type":             tc.type.value,
                    "priority":         tc.priority.value,
                    "preconditions":    tc.preconditions,
                    "steps": [
                        {
                            "step_number":    s.step_number,
                            "action":         s.action,
                            "expected_result":s.expected_result,
                        } for s in tc.steps
                    ],
                    "expected_outcome": tc.expected_outcome,
                    "tags":             tc.tags,
                }
                for tc in result.test_cases
            ]
        }

        content  = json.dumps(payload, indent=2)
        filename = f"test_cases_{self._slugify(result.ui_description)}_{result.session_id[:8]}.json"

        return ExportResponse(
            session_id       = result.session_id,
            export_format    = "json",
            filename         = filename,
            content          = content,
            total_test_cases = result.total_count,
        )

    # ── CSV export ─────────────────────────────────────────────────────────────

    def to_csv(self, result: GenerationResult) -> ExportResponse:
        buffer = io.StringIO()
        writer = csv.writer(buffer, quoting=csv.QUOTE_ALL)

        # Header
        writer.writerow([
            "ID", "Title", "Type", "Priority",
            "Preconditions", "Steps Summary",
            "Expected Outcome", "Tags"
        ])

        for tc in result.test_cases:
            preconditions_str = " | ".join(tc.preconditions)
            steps_str = " | ".join(
                f"Step {s.step_number}: {s.action} → {s.expected_result}"
                for s in tc.steps
            )
            tags_str = ", ".join(tc.tags)

            writer.writerow([
                tc.id,
                tc.title,
                tc.type.value,
                tc.priority.value,
                preconditions_str,
                steps_str,
                tc.expected_outcome,
                tags_str,
            ])

        content  = buffer.getvalue()
        filename = f"test_cases_{self._slugify(result.ui_description)}_{result.session_id[:8]}.csv"

        return ExportResponse(
            session_id       = result.session_id,
            export_format    = "csv",
            filename         = filename,
            content          = content,
            total_test_cases = result.total_count,
        )


export_service = ExportService()