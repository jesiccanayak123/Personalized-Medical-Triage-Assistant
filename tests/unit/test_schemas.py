"""
Unit tests for Pydantic schemas/models validation.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from modules.triage.schemas import (
    InterviewerOutput,
    RiskAssessmentOutput,
    ICD10CodingOutput,
    SOAPNoteOutput,
    UIResponse,
    RedFlag,
    ICD10Code,
)
from modules.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
)
from modules.patients.schemas import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
)


class TestTriageSchemas:
    """Tests for triage-related schemas."""

    def test_interviewer_output_valid(self):
        """Test valid InterviewerOutput creation."""
        output = InterviewerOutput(
            question="What symptoms are you experiencing?",
            gathered_info={"chief_complaint": "headache"},
            missing_fields=["duration", "severity"],
            is_done=False,
        )
        
        assert output.question == "What symptoms are you experiencing?"
        assert output.is_done is False
        assert len(output.missing_fields) == 2

    def test_interviewer_output_done(self):
        """Test InterviewerOutput when interview is done."""
        output = InterviewerOutput(
            question=None,
            gathered_info={
                "chief_complaint": "headache",
                "duration": "2 hours",
                "severity": 5,
            },
            missing_fields=[],
            is_done=True,
        )
        
        assert output.is_done is True
        assert output.question is None

    def test_risk_assessment_emergency(self):
        """Test RiskAssessmentOutput for emergency."""
        output = RiskAssessmentOutput(
            is_emergency=True,
            disposition="EMERGENCY",
            confidence=0.95,
            red_flags=[
                RedFlag(label="chest_pain", evidence="crushing chest pain"),
                RedFlag(label="breathing", evidence="shortness of breath"),
            ],
            reasoning="Patient exhibits classic cardiac symptoms",
        )
        
        assert output.is_emergency is True
        assert output.disposition == "EMERGENCY"
        assert len(output.red_flags) == 2

    def test_risk_assessment_routine(self):
        """Test RiskAssessmentOutput for routine case."""
        output = RiskAssessmentOutput(
            is_emergency=False,
            disposition="ROUTINE",
            confidence=0.85,
            red_flags=[],
            reasoning="Mild symptoms with no concerning features",
        )
        
        assert output.is_emergency is False
        assert output.disposition == "ROUTINE"

    def test_icd10_code_valid(self):
        """Test valid ICD10Code creation."""
        code = ICD10Code(
            icd10="R51.9",
            description="Headache, unspecified",
            confidence=0.9,
            evidence="Patient reports persistent headache",
            source_ids=["doc_123", "doc_456"],
        )
        
        assert code.icd10 == "R51.9"
        assert code.confidence == 0.9

    def test_icd10_coding_output(self):
        """Test ICD10CodingOutput with multiple codes."""
        output = ICD10CodingOutput(
            codes=[
                ICD10Code(
                    icd10="R51.9",
                    description="Headache, unspecified",
                    confidence=0.9,
                    evidence="Patient reports headache",
                ),
                ICD10Code(
                    icd10="G43.909",
                    description="Migraine, unspecified",
                    confidence=0.7,
                    evidence="Pattern suggests migraine",
                ),
            ],
            primary_code="R51.9",
            reasoning="Primary complaint is headache",
        )
        
        assert len(output.codes) == 2
        assert output.primary_code == "R51.9"

    def test_soap_note_output(self):
        """Test SOAPNoteOutput creation."""
        output = SOAPNoteOutput(
            subjective={
                "chief_complaint": "Headache",
                "history": "Started 2 hours ago",
                "associated_symptoms": ["nausea"],
            },
            objective={
                "vital_signs": "Not available",
                "physical_exam": "Telehealth encounter",
            },
            assessment={
                "primary_diagnosis": "Tension headache",
                "differential": ["Migraine", "Cluster headache"],
            },
            plan={
                "treatment": "OTC pain relievers",
                "follow_up": "If symptoms persist beyond 48 hours",
            },
        )
        
        assert "chief_complaint" in output.subjective
        assert "primary_diagnosis" in output.assessment

    def test_ui_response_normal(self):
        """Test UIResponse for normal interaction."""
        response = UIResponse(
            message="What other symptoms are you experiencing?",
            status="INTERVIEWING",
            is_emergency=False,
        )
        
        assert response.is_emergency is False
        assert response.status == "INTERVIEWING"

    def test_ui_response_emergency(self):
        """Test UIResponse for emergency."""
        response = UIResponse(
            message="EMERGENCY: Please call 911 immediately.",
            status="EMERGENCY",
            is_emergency=True,
            risk_assessment=RiskAssessmentOutput(
                is_emergency=True,
                disposition="EMERGENCY",
                confidence=0.99,
                red_flags=[RedFlag(label="cardiac", evidence="chest pain")],
            ),
        )
        
        assert response.is_emergency is True
        assert response.risk_assessment is not None


class TestAuthSchemas:
    """Tests for authentication schemas."""

    def test_register_request_valid(self):
        """Test valid registration request."""
        request = RegisterRequest(
            email="test@example.com",
            password="secure123password",
            name="Test User",
        )
        
        assert request.email == "test@example.com"
        assert request.name == "Test User"

    def test_register_request_invalid_email(self):
        """Test registration with invalid email."""
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="not-an-email",
                password="secure123",
                name="Test",
            )

    def test_register_request_short_password(self):
        """Test registration with short password."""
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@example.com",
                password="123",
                name="Test",
            )

    def test_login_request_valid(self):
        """Test valid login request."""
        request = LoginRequest(
            email="test@example.com",
            password="password123",
        )
        
        assert request.email == "test@example.com"

    def test_user_response(self):
        """Test user response serialization."""
        response = UserResponse(
            id="abc123def456",
            email="test@example.com",
            name="Test User",
            is_active=True,
            created_at=datetime.utcnow(),
        )
        
        assert response.id == "abc123def456"
        assert response.is_active is True


class TestPatientSchemas:
    """Tests for patient schemas."""

    def test_patient_create_valid(self):
        """Test valid patient creation."""
        patient = PatientCreate(
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-15",
            gender="male",
            phone="555-123-4567",
            email="john@example.com",
        )
        
        assert patient.first_name == "John"
        assert patient.last_name == "Doe"

    def test_patient_create_minimal(self):
        """Test patient creation with minimal fields."""
        patient = PatientCreate(
            first_name="Jane",
            last_name="Smith",
        )
        
        assert patient.first_name == "Jane"
        assert patient.date_of_birth is None

    def test_patient_update_partial(self):
        """Test partial patient update."""
        update = PatientUpdate(
            phone="555-987-6543",
        )
        
        assert update.phone == "555-987-6543"
        assert update.first_name is None

    def test_patient_response(self):
        """Test patient response serialization."""
        response = PatientResponse(
            id="patient123",
            user_id="user456",
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-15",
            gender="male",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        assert response.id == "patient123"
        assert response.first_name == "John"


class TestSchemaValidation:
    """Tests for schema validation edge cases."""

    def test_confidence_bounds(self):
        """Test confidence score bounds."""
        # Valid confidence
        code = ICD10Code(
            icd10="R51.9",
            description="Headache",
            confidence=0.5,
            evidence="test",
        )
        assert code.confidence == 0.5

        # Boundary values
        code_low = ICD10Code(
            icd10="R51.9",
            description="Headache",
            confidence=0.0,
            evidence="test",
        )
        assert code_low.confidence == 0.0

        code_high = ICD10Code(
            icd10="R51.9",
            description="Headache",
            confidence=1.0,
            evidence="test",
        )
        assert code_high.confidence == 1.0

    def test_empty_lists_allowed(self):
        """Test that empty lists are allowed where appropriate."""
        output = InterviewerOutput(
            question="Test?",
            gathered_info={},
            missing_fields=[],
            is_done=False,
        )
        
        assert output.missing_fields == []

    def test_none_vs_empty_string(self):
        """Test handling of None vs empty string."""
        # None should be allowed for optional fields
        output = InterviewerOutput(
            question=None,
            gathered_info={},
            missing_fields=[],
            is_done=True,
        )
        
        assert output.question is None

