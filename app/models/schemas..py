import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum
import uuid
from datetime import datetime


class TestCaseType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    EDGE_CASE = "edge_case"


class TestCasePriority(str, Enum):
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"


# ── Request ────────────────────────────────────────────────────────────────────

class TestCaseRequest(BaseModel):
    ui_description: str = Field(
        ...,
        min_length=20,
        description="Natural language description of the UI component or screen",
        example="A login form with email, password fields and a submit button"
    )
    product_requirements: str = Field(
        ...,
        min_length=20,
        description="Functional requirements / acceptance criteria",
        example="User must be authenticated. Email must be valid. Password min 8 chars."
    )
    test_types: list[TestCaseType] = Field(
        default=[TestCaseType.POSITIVE, TestCaseType.NEGATIVE, TestCaseType.EDGE_CASE],
        description="Which test scenario types to generate"
    )
    max_per_type: Optional[int] = Field(
        default=5, ge=1, le=10,
        description="Max test cases per type"
    )


# ── Core test case model ───────────────────────────────────────────────────────

class TestStep(BaseModel):
    step_number: int
    action: str
    expected_result: str


class TestCase(BaseModel):
    id: str                         = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    type: TestCaseType
    priority: TestCasePriority      = TestCasePriority.MEDIUM
    preconditions: list[str]        = []
    steps: list[TestStep]           = []
    expected_outcome: str           = ""
    tags: list[str]                 = []


# ── Response ───────────────────────────────────────────────────────────────────

class GenerationResult(BaseModel):
    session_id: str                 = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime          = Field(default_factory=datetime.utcnow)
    ui_description: str
    product_requirements: str
    test_cases: list[TestCase]      = []
    total_count: int                = 0
    positive_count: int             = 0
    negative_count: int             = 0
    edge_case_count: int            = 0

    def compute_counts(self):
        self.total_count    = len(self.test_cases)
        self.positive_count = sum(1 for t in self.test_cases if t.type == TestCaseType.POSITIVE)
        self.negative_count = sum(1 for t in self.test_cases if t.type == TestCaseType.NEGATIVE)
        self.edge_case_count= sum(1 for t in self.test_cases if t.type == TestCaseType.EDGE_CASE)
        return self


class ExportResponse(BaseModel):
    session_id: str
    export_format: Literal["json", "csv"]
    filename: str
    content: str                    # raw file content as string
    total_test_cases: int