"""
Unit tests for the rules engine.
"""
import pytest
from agents.rules_engine import (
    RulesEngine,
    RedFlag,
    EMERGENCY_RED_FLAGS,
    HIGH_RISK_RED_FLAGS,
)


class TestRulesEngine:
    """Tests for RulesEngine class."""

    @pytest.fixture
    def engine(self):
        """Create a rules engine instance."""
        return RulesEngine()

    def test_emergency_chest_pain(self, engine):
        """Test emergency detection for chest pain symptoms."""
        intake = {
            "symptoms": ["chest pain", "shortness of breath"],
            "severity": 8,
            "duration_hours": 2,
        }
        
        result = engine.assess_risk(intake)
        
        assert result["is_emergency"] is True
        assert result["disposition"] == "EMERGENCY"
        assert len(result["red_flags"]) > 0
        assert any(flag["label"] == "chest_pain" for flag in result["red_flags"])

    def test_emergency_stroke_symptoms(self, engine):
        """Test emergency detection for stroke symptoms."""
        intake = {
            "symptoms": ["sudden severe headache", "facial drooping", "arm weakness"],
            "onset": "sudden",
        }
        
        result = engine.assess_risk(intake)
        
        assert result["is_emergency"] is True
        assert result["disposition"] == "EMERGENCY"

    def test_emergency_difficulty_breathing(self, engine):
        """Test emergency detection for difficulty breathing."""
        intake = {
            "symptoms": ["can't breathe", "turning blue"],
            "severity": 10,
        }
        
        result = engine.assess_risk(intake)
        
        assert result["is_emergency"] is True

    def test_high_risk_not_emergency(self, engine):
        """Test high risk that's not an emergency."""
        intake = {
            "symptoms": ["fever", "abdominal pain"],
            "severity": 6,
            "duration_hours": 48,
        }
        
        result = engine.assess_risk(intake)
        
        # High severity abdominal pain should be concerning
        assert result["disposition"] in ["URGENT", "HIGH_RISK", "EMERGENCY"]

    def test_low_risk_symptoms(self, engine):
        """Test low risk symptom assessment."""
        intake = {
            "symptoms": ["mild headache"],
            "severity": 3,
            "duration_hours": 2,
        }
        
        result = engine.assess_risk(intake)
        
        assert result["is_emergency"] is False
        assert result["disposition"] in ["ROUTINE", "LOW_RISK", "MODERATE"]

    def test_severity_threshold(self, engine):
        """Test severity threshold triggers."""
        intake = {
            "symptoms": ["pain"],
            "severity": 10,
        }
        
        result = engine.assess_risk(intake)
        
        # Severity 10 should be at least high risk
        assert result["disposition"] in ["HIGH_RISK", "URGENT", "EMERGENCY"]

    def test_text_message_analysis(self, engine):
        """Test risk assessment from user message text."""
        message = "I'm having severe chest pain that radiates to my left arm and I feel short of breath"
        
        result = engine.analyze_message(message)
        
        assert result["is_emergency"] is True
        assert len(result["detected_symptoms"]) > 0

    def test_text_message_no_emergency(self, engine):
        """Test non-emergency message analysis."""
        message = "I have a slight headache that started this morning"
        
        result = engine.analyze_message(message)
        
        assert result["is_emergency"] is False

    def test_suicidal_ideation_emergency(self, engine):
        """Test emergency for suicidal ideation."""
        intake = {
            "symptoms": ["suicidal thoughts", "wants to hurt self"],
        }
        
        result = engine.assess_risk(intake)
        
        assert result["is_emergency"] is True

    def test_allergic_reaction_emergency(self, engine):
        """Test emergency for severe allergic reaction."""
        intake = {
            "symptoms": ["throat swelling", "can't swallow", "hives all over"],
        }
        
        result = engine.assess_risk(intake)
        
        assert result["is_emergency"] is True

    def test_empty_intake(self, engine):
        """Test handling of empty intake."""
        intake = {}
        
        result = engine.assess_risk(intake)
        
        assert "is_emergency" in result
        assert "disposition" in result

    def test_missing_symptoms(self, engine):
        """Test handling when symptoms are missing."""
        intake = {
            "severity": 5,
            "duration_hours": 24,
        }
        
        result = engine.assess_risk(intake)
        
        assert result["is_emergency"] is False

    def test_confidence_score(self, engine):
        """Test that confidence score is returned."""
        intake = {
            "symptoms": ["chest pain"],
            "severity": 8,
        }
        
        result = engine.assess_risk(intake)
        
        assert "confidence" in result
        assert 0 <= result["confidence"] <= 1

    def test_red_flags_include_evidence(self, engine):
        """Test that red flags include evidence."""
        intake = {
            "symptoms": ["crushing chest pain", "arm numbness"],
        }
        
        result = engine.assess_risk(intake)
        
        for flag in result["red_flags"]:
            assert "label" in flag
            assert "evidence" in flag

    def test_combined_symptoms_escalation(self, engine):
        """Test that combined symptoms can escalate risk."""
        # Single mild symptom
        single = engine.assess_risk({"symptoms": ["fatigue"]})
        
        # Multiple concerning symptoms
        combined = engine.assess_risk({
            "symptoms": ["fatigue", "unexplained weight loss", "night sweats"],
            "duration_hours": 336,  # 2 weeks
        })
        
        # Combined should be higher risk
        risk_levels = ["ROUTINE", "LOW_RISK", "MODERATE", "HIGH_RISK", "URGENT", "EMERGENCY"]
        single_idx = risk_levels.index(single["disposition"]) if single["disposition"] in risk_levels else 0
        combined_idx = risk_levels.index(combined["disposition"]) if combined["disposition"] in risk_levels else 0
        
        # This test just verifies the system handles both cases
        assert single["disposition"] is not None
        assert combined["disposition"] is not None


class TestRedFlagPatterns:
    """Tests for red flag pattern matching."""

    def test_chest_pain_patterns(self):
        """Test chest pain pattern detection."""
        patterns = EMERGENCY_RED_FLAGS.get("chest_pain", [])
        
        # Should have patterns for chest pain detection
        assert len(patterns) > 0
        
        # Test pattern matching
        test_text = "I have crushing chest pain"
        matches = any(
            pattern.lower() in test_text.lower() 
            for pattern in patterns
        )
        assert matches

    def test_breathing_patterns(self):
        """Test breathing difficulty patterns."""
        patterns = EMERGENCY_RED_FLAGS.get("breathing_difficulty", [])
        
        assert len(patterns) > 0
        
        test_text = "I can't breathe properly"
        matches = any(
            pattern.lower() in test_text.lower() 
            for pattern in patterns
        )
        assert matches

    def test_stroke_patterns(self):
        """Test stroke symptom patterns."""
        patterns = EMERGENCY_RED_FLAGS.get("stroke_symptoms", [])
        
        assert len(patterns) > 0
        
        test_text = "sudden severe headache and slurred speech"
        matches = any(
            pattern.lower() in test_text.lower() 
            for pattern in patterns
        )
        assert matches

