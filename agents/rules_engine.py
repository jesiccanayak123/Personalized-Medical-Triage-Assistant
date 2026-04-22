"""Deterministic rules engine for emergency detection.

This runs BEFORE the LLM-based risk assessor to catch critical emergencies
with hard-coded rules that don't require LLM inference.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from modules.triage.schemas import RedFlag, RiskAssessmentOutput, DispositionLevel


@dataclass
class EmergencyRule:
    """Emergency detection rule."""
    rule_id: str
    label: str
    patterns: List[str]  # Regex patterns
    severity: str  # CRITICAL, HIGH, MEDIUM
    emergency: bool
    recommended_action: str


# Hard-coded emergency rules
EMERGENCY_RULES: List[EmergencyRule] = [
    EmergencyRule(
        rule_id="RF001_CHEST_PAIN_CARDIAC",
        label="Possible cardiac emergency",
        patterns=[
            r"chest\s*(pain|pressure|tightness).*\b(arm|jaw|neck|shoulder)\b",
            r"\b(arm|jaw|neck|shoulder)\b.*chest\s*(pain|pressure|tightness)",
            r"chest\s*(pain|pressure).*short(ness)?\s*of\s*breath",
            r"crushing.*chest",
            r"elephant.*chest",
        ],
        severity="CRITICAL",
        emergency=True,
        recommended_action="call_911_cardiac",
    ),
    EmergencyRule(
        rule_id="RF002_STROKE_FAST",
        label="Possible stroke - FAST symptoms",
        patterns=[
            r"(face|facial).*(droop|numb|weak)",
            r"(arm|leg).*(weak|numb|can\'?t\s*move|paralyz)",
            r"(speech|talk).*(slur|confus|difficult|trouble)",
            r"sudden.*(headache|worst.*head)",
            r"sudden.*(numb|weak|paralyz)",
        ],
        severity="CRITICAL",
        emergency=True,
        recommended_action="call_911_stroke",
    ),
    EmergencyRule(
        rule_id="RF003_BREATHING_SEVERE",
        label="Severe breathing difficulty",
        patterns=[
            r"can\'?t\s*breath",
            r"(hard|difficult|trouble)\s*(to\s*)?(breath|breathing)",
            r"gasping",
            r"lips?.*(blue|purple)",
            r"turning\s*blue",
        ],
        severity="CRITICAL",
        emergency=True,
        recommended_action="call_911_respiratory",
    ),
    EmergencyRule(
        rule_id="RF004_ANAPHYLAXIS",
        label="Possible anaphylaxis",
        patterns=[
            r"(throat|tongue).*(swell|tight|clos)",
            r"(hives|rash).*breath",
            r"allergic.*react.*breath",
            r"epipen",
        ],
        severity="CRITICAL",
        emergency=True,
        recommended_action="call_911_anaphylaxis",
    ),
    EmergencyRule(
        rule_id="RF005_UNCONSCIOUS",
        label="Loss of consciousness",
        patterns=[
            r"(pass|black)\s*out",
            r"(lost|lose|losing)\s*conscious",
            r"unresponsive",
            r"faint(ed|ing)?",
            r"collaps(e|ed|ing)",
        ],
        severity="CRITICAL",
        emergency=True,
        recommended_action="call_911_unconscious",
    ),
    EmergencyRule(
        rule_id="RF006_SUICIDAL",
        label="Mental health emergency",
        patterns=[
            r"(want|think).*(die|kill|end)",
            r"suicid(e|al)",
            r"hurt.*myself",
            r"self.?harm",
        ],
        severity="CRITICAL",
        emergency=True,
        recommended_action="call_988_mental_health",
    ),
    EmergencyRule(
        rule_id="RF007_SEVERE_BLEEDING",
        label="Severe bleeding",
        patterns=[
            r"(can\'?t|won\'?t)\s*stop\s*bleed",
            r"blood\s*(everywhere|gushing|spurting)",
            r"severe\s*bleed",
        ],
        severity="CRITICAL",
        emergency=True,
        recommended_action="call_911_trauma",
    ),
    EmergencyRule(
        rule_id="RF008_HIGH_FEVER",
        label="High fever",
        patterns=[
            r"(fever|temp).*(103|104|105|106)",
            r"(39\.5|39\.[6-9]|40\.[0-9]|41\.[0-9]).*[cC]",
        ],
        severity="HIGH",
        emergency=False,
        recommended_action="seek_urgent_care",
    ),
]


class RulesEngine:
    """Deterministic rules engine for emergency detection."""

    def __init__(self, rules: Optional[List[EmergencyRule]] = None):
        """Initialize the rules engine.
        
        Args:
            rules: Optional custom rules list
        """
        self.rules = rules or EMERGENCY_RULES

    def evaluate(self, text: str) -> RiskAssessmentOutput:
        """Evaluate text against emergency rules.
        
        Args:
            text: Text to evaluate (conversation or symptoms)
            
        Returns:
            RiskAssessmentOutput with detected red flags
        """
        text_lower = text.lower()
        red_flags: List[RedFlag] = []
        is_emergency = False
        max_severity = "LOW"
        recommended_action = None

        for rule in self.rules:
            for pattern in rule.patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    red_flags.append(RedFlag(
                        rule_id=rule.rule_id,
                        label=rule.label,
                        matched_text=match.group(0),
                        severity=rule.severity,
                    ))
                    
                    if rule.emergency:
                        is_emergency = True
                    
                    # Track highest severity
                    if rule.severity == "CRITICAL":
                        max_severity = "CRITICAL"
                    elif rule.severity == "HIGH" and max_severity != "CRITICAL":
                        max_severity = "HIGH"
                    
                    # Set recommended action from first critical rule
                    if rule.emergency and not recommended_action:
                        recommended_action = rule.recommended_action
                    
                    break  # Only match once per rule

        # Determine disposition
        if is_emergency:
            disposition = DispositionLevel.EMERGENT
        elif max_severity == "HIGH":
            disposition = DispositionLevel.URGENT
        elif red_flags:
            disposition = DispositionLevel.LESS_URGENT
        else:
            disposition = DispositionLevel.NON_URGENT

        return RiskAssessmentOutput(
            emergency=is_emergency,
            red_flags=red_flags,
            disposition=disposition,
            ui_interrupt=is_emergency,
            recommended_action_template_id=recommended_action,
        )

    def check_emergency(self, text: str) -> bool:
        """Quick check if text contains emergency patterns.
        
        Args:
            text: Text to check
            
        Returns:
            True if emergency detected
        """
        result = self.evaluate(text)
        return result.emergency

    def analyze_message(self, text: str) -> Dict[str, Any]:
        """Analyze a message for emergency symptoms.
        
        Returns a dict format for easy JSON serialization.
        
        Args:
            text: User message text
            
        Returns:
            Dict with is_emergency, red_flags, detected_symptoms, etc.
        """
        result = self.evaluate(text)
        
        return {
            "is_emergency": result.emergency,
            "disposition": result.disposition.value if result.disposition else "ROUTINE",
            "confidence": 0.95 if result.emergency else 0.7,
            "red_flags": [
                {
                    "rule_id": rf.rule_id,
                    "label": rf.label,
                    "evidence": rf.matched_text,
                    "severity": rf.severity,
                }
                for rf in result.red_flags
            ],
            "detected_symptoms": [rf.matched_text for rf in result.red_flags],
            "recommended_action": result.recommended_action_template_id,
        }

    def assess_risk(self, intake: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk from intake data structure.
        
        Args:
            intake: Structured intake data with symptoms, severity, etc.
            
        Returns:
            Dict with risk assessment results
        """
        # Build text from intake
        parts = []
        
        if "symptoms" in intake:
            symptoms = intake["symptoms"]
            if isinstance(symptoms, list):
                parts.append(" ".join(symptoms))
            else:
                parts.append(str(symptoms))
        
        if "chief_complaint" in intake:
            parts.append(str(intake["chief_complaint"]))
        
        text = " ".join(parts)
        
        # Run analysis
        result = self.analyze_message(text)
        
        # Check severity threshold
        severity = intake.get("severity", 0)
        if isinstance(severity, (int, float)) and severity >= 9:
            result["is_emergency"] = True
            result["disposition"] = "EMERGENCY"
            result["red_flags"].append({
                "rule_id": "RF_SEVERITY",
                "label": "High severity rating",
                "evidence": f"Severity rated {severity}/10",
                "severity": "CRITICAL",
            })
        
        return result


# Global instance
rules_engine = RulesEngine()


# For test compatibility - expose the emergency patterns
EMERGENCY_RED_FLAGS = {
    "chest_pain": [
        "chest pain", "chest pressure", "crushing chest", 
        "chest tightness", "pain in chest"
    ],
    "breathing_difficulty": [
        "can't breathe", "hard to breathe", "trouble breathing",
        "shortness of breath", "difficulty breathing", "gasping"
    ],
    "stroke_symptoms": [
        "sudden severe headache", "slurred speech", "facial drooping",
        "arm weakness", "sudden numbness", "worst headache"
    ],
}

HIGH_RISK_RED_FLAGS = {
    "high_fever": ["fever 103", "fever 104", "high fever"],
    "severe_pain": ["severe pain", "worst pain", "10 out of 10"],
}

