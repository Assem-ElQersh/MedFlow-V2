import random
import time
from typing import Dict, List, Any
from datetime import datetime


class MockVLMService:
    """Mock VLM service that generates realistic medical findings"""
    
    # Medical knowledge base for mock responses
    RESPIRATORY_FINDINGS = [
        "Chest X-ray shows clear lung fields bilaterally",
        "No evidence of pulmonary infiltrates or consolidation",
        "Mild bronchial wall thickening suggesting reactive airway component",
        "Cardiothoracic ratio within normal limits",
        "No pleural effusion or pneumothorax identified",
    ]
    
    CARDIAC_FINDINGS = [
        "Normal cardiac silhouette",
        "No evidence of cardiomegaly",
        "Aortic arch appears normal",
        "No signs of pulmonary edema",
    ]
    
    SYMPTOM_PATTERNS = {
        "cough": {
            "observations": ["Prolonged cough duration", "Pattern suggests viral or reactive etiology"],
            "considerations": ["Viral bronchitis", "Reactive airway disease", "Post-viral cough syndrome"],
            "differential": ["Viral upper respiratory infection", "Asthma exacerbation", "Chronic bronchitis"]
        },
        "chest pain": {
            "observations": ["Location and radiation pattern noted", "Character of pain important for diagnosis"],
            "considerations": ["Cardiac evaluation needed", "Musculoskeletal component possible", "Gastroesophageal causes"],
            "differential": ["Angina pectoris", "Costochondritis", "GERD", "Anxiety-related"]
        },
        "fever": {
            "observations": ["Duration and pattern of fever", "Associated symptoms relevant"],
            "considerations": ["Infectious process likely", "Need to rule out bacterial infection"],
            "differential": ["Viral infection", "Bacterial infection", "Inflammatory condition"]
        },
        "headache": {
            "observations": ["Onset and progression pattern", "Associated neurological symptoms"],
            "considerations": ["Tension-type vs migraine", "Red flags for serious pathology"],
            "differential": ["Tension headache", "Migraine", "Sinusitis", "Cluster headache"]
        },
        "abdominal pain": {
            "observations": ["Location and character of pain", "Associated GI symptoms"],
            "considerations": ["Acute abdomen evaluation", "Organ-specific pathology"],
            "differential": ["Gastritis", "Peptic ulcer", "Appendicitis", "Cholecystitis"]
        }
    }
    
    def __init__(self):
        self.model_version = "medgemma-v2.1-mock"
    
    def process_initial_session(
        self,
        patient_context: Dict[str, Any],
        chief_complaint: str,
        current_state: str,
        last_session_summary: str = None,
        files_count: int = 0
    ) -> Dict[str, Any]:
        """Generate mock VLM initial output for a session"""
        
        # Simulate processing time
        start_time = time.time()
        time.sleep(random.uniform(2, 5))  # Simulate 2-5 seconds processing
        
        # Extract keywords from chief complaint
        complaint_lower = chief_complaint.lower()
        
        # Determine which symptom pattern to use
        primary_symptom = None
        for symptom in self.SYMPTOM_PATTERNS.keys():
            if symptom in complaint_lower:
                primary_symptom = symptom
                break
        
        # Generate findings based on patient context
        findings = self._generate_findings(
            patient_context,
            chief_complaint,
            current_state,
            primary_symptom,
            files_count
        )
        
        # Generate key observations
        key_observations = self._generate_observations(
            patient_context,
            primary_symptom
        )
        
        # Generate technical assessment
        technical_assessment = self._generate_technical_assessment(
            patient_context,
            files_count,
            primary_symptom
        )
        
        # Generate suggested considerations
        suggested_considerations = self._generate_considerations(
            patient_context,
            primary_symptom
        )
        
        # Generate differential patterns
        differential_patterns = self._generate_differential(
            patient_context,
            primary_symptom
        )
        
        processing_time = int(time.time() - start_time)
        
        return {
            "findings": findings,
            "key_observations": key_observations,
            "technical_assessment": technical_assessment,
            "suggested_considerations": suggested_considerations,
            "differential_patterns": differential_patterns,
            "model_version": self.model_version,
            "processing_time_seconds": processing_time
        }
    
    def process_doctor_query(
        self,
        patient_context: Dict[str, Any],
        session_context: Dict[str, Any],
        doctor_query: str,
        previous_chat: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate mock VLM response to doctor's question"""
        
        start_time = time.time()
        time.sleep(random.uniform(1, 3))  # Simulate 1-3 seconds processing
        
        query_lower = doctor_query.lower()
        
        # Generate contextual response based on query
        if any(word in query_lower for word in ["pain", "radiating", "shoulder"]):
            findings = (
                "Pain radiation pattern is noteworthy. Left shoulder pain with chest symptoms "
                "may suggest cardiac referral pain (Kehr's sign consideration) or musculoskeletal "
                "origin. Given patient context, would recommend: 1) ECG if not done recently, "
                "2) Cardiac enzyme panel, 3) Physical exam focusing on chest wall tenderness."
            )
        elif any(word in query_lower for word in ["bp", "blood pressure", "hypertension"]):
            findings = (
                f"Blood pressure of {doctor_query.split()[-1] if 'mmHg' in doctor_query else '145/90'} "
                "is elevated. Considering patient's chronic conditions, this warrants attention. "
                "Recommend: 1) Repeat measurement after rest, 2) Review current antihypertensive "
                "regimen if applicable, 3) Consider workup for acute causes if persistently elevated."
            )
        elif any(word in query_lower for word in ["wheez", "breath", "respiratory"]):
            findings = (
                "Wheezing on auscultation suggests bronchospasm component. This supports reactive "
                "airway involvement. Consider: 1) Trial of bronchodilator therapy, 2) Assess for "
                "triggers (allergens, irritants), 3) Pulmonary function testing if symptoms persist."
            )
        else:
            findings = (
                "Based on the additional clinical information provided, the presentation remains "
                "consistent with the initial differential diagnosis. Key points to consider: "
                "1) Monitor symptom progression, 2) Consider additional diagnostic workup if symptoms "
                "worsen, 3) Patient education regarding warning signs."
            )
        
        processing_time = int(time.time() - start_time)
        
        return {
            "findings": findings,
            "processing_time": processing_time
        }
    
    def _generate_findings(
        self,
        patient_context: Dict,
        chief_complaint: str,
        current_state: str,
        primary_symptom: str,
        files_count: int
    ) -> str:
        """Generate comprehensive findings"""
        
        findings_parts = []
        
        # Patient context
        age = patient_context.get("age", "unknown")
        sex = patient_context.get("sex", "unknown")
        findings_parts.append(
            f"Patient is a {age}-year-old {sex} presenting with {chief_complaint.lower()}."
        )
        
        # Image findings if files uploaded
        if files_count > 0:
            if "cough" in chief_complaint.lower() or "chest" in chief_complaint.lower():
                findings_parts.extend(self.RESPIRATORY_FINDINGS[:3])
            if "chest" in chief_complaint.lower() or "heart" in chief_complaint.lower():
                findings_parts.extend(self.CARDIAC_FINDINGS[:2])
        
        # Clinical assessment
        findings_parts.append(
            "Clinical presentation and available imaging suggest a likely diagnosis that should "
            "be correlated with physical examination findings and patient's symptom progression."
        )
        
        # Chronic disease considerations
        chronic_diseases = patient_context.get("chronic_diseases", [])
        if chronic_diseases:
            findings_parts.append(
                f"Given patient's history of {', '.join(chronic_diseases)}, careful monitoring "
                "and management optimization may be indicated."
            )
        
        return " ".join(findings_parts)
    
    def _generate_observations(self, patient_context: Dict, primary_symptom: str) -> List[str]:
        """Generate key observations"""
        observations = [
            f"Patient age {patient_context.get('age')} years - age-appropriate differential considered",
            "Symptom duration and progression pattern noted",
        ]
        
        if primary_symptom and primary_symptom in self.SYMPTOM_PATTERNS:
            observations.extend(self.SYMPTOM_PATTERNS[primary_symptom]["observations"])
        else:
            observations.extend([
                "Clinical presentation requires comprehensive evaluation",
                "Multiple system review may be warranted"
            ])
        
        # Add chronic disease observation if relevant
        if patient_context.get("chronic_diseases"):
            observations.append("Chronic disease management should be integrated into treatment plan")
        
        return observations[:5]  # Return top 5
    
    def _generate_technical_assessment(
        self,
        patient_context: Dict,
        files_count: int,
        primary_symptom: str
    ) -> str:
        """Generate technical assessment"""
        
        if files_count > 0:
            return (
                f"Analysis of {files_count} uploaded medical file(s) completed. "
                "Imaging quality adequate for diagnostic interpretation. "
                "Key findings extracted and integrated with clinical presentation. "
                "No critical abnormalities requiring immediate intervention identified. "
                "Recommend clinical correlation with physical examination."
            )
        else:
            return (
                "Clinical assessment based on patient history and symptoms. "
                "Consider diagnostic imaging if clinically indicated. "
                "Physical examination findings will be crucial for diagnosis confirmation."
            )
    
    def _generate_considerations(self, patient_context: Dict, primary_symptom: str) -> List[str]:
        """Generate suggested considerations"""
        considerations = []
        
        if primary_symptom and primary_symptom in self.SYMPTOM_PATTERNS:
            considerations.extend(self.SYMPTOM_PATTERNS[primary_symptom]["considerations"])
        else:
            considerations = [
                "Comprehensive clinical evaluation recommended",
                "Consider relevant diagnostic workup",
                "Monitor symptom progression closely"
            ]
        
        # Add medication interaction consideration
        if patient_context.get("current_medications"):
            considerations.append("Review current medications for potential interactions")
        
        return considerations[:4]
    
    def _generate_differential(self, patient_context: Dict, primary_symptom: str) -> List[str]:
        """Generate differential diagnosis patterns"""
        
        if primary_symptom and primary_symptom in self.SYMPTOM_PATTERNS:
            return self.SYMPTOM_PATTERNS[primary_symptom]["differential"]
        else:
            return [
                "Differential diagnosis to be refined with physical examination",
                "Multiple etiologies possible based on presentation",
                "Clinical correlation essential for accurate diagnosis"
            ]


# Singleton instance
mock_vlm_service = MockVLMService()

