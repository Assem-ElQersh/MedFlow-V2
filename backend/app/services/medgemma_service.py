"""
MedGemma VLM Service using Hugging Face Inference API
"""
import time
from typing import Dict, List, Any, Optional
from huggingface_hub import InferenceClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class MedGemmaService:
    """Real MedGemma VLM service using Hugging Face Inference API with fallback"""
    
    def __init__(self):
        self.primary_model = settings.MEDGEMMA_MODEL
        self.fallback_model = settings.BIOGPT_MODEL
        self.client = InferenceClient(token=settings.HF_TOKEN)
        logger.info(f"Initialized MedGemma service - Primary: {self.primary_model}, Fallback: {self.fallback_model}")
    
    def process_initial_session(
        self,
        patient_context: Dict[str, Any],
        chief_complaint: str,
        current_state: str,
        last_session_summary: Optional[str] = None,
        files_count: int = 0
    ) -> Dict[str, Any]:
        """Generate VLM initial output for a session using MedGemma with fallback to BioGPT"""
        
        start_time = time.time()
        
        # Try primary model first (MedGemma-4B)
        try:
            # Construct medical prompt
            prompt = self._build_initial_prompt(
                patient_context,
                chief_complaint,
                current_state,
                last_session_summary,
                files_count
            )
            
            logger.info(f"Trying primary model {self.primary_model} (prompt length: {len(prompt)} chars)")
            
            # Call Hugging Face Inference API with primary model
            response = self.client.text_generation(
                prompt,
                model=self.primary_model,
                max_new_tokens=1000,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1,
            )
            
            logger.info(f"SUCCESS: Received response from {self.primary_model} (length: {len(response)} chars)")
            
            # Parse the response into structured format
            parsed_output = self._parse_initial_response(response, patient_context, chief_complaint)
            
            processing_time = int(time.time() - start_time)
            parsed_output["processing_time_seconds"] = processing_time
            parsed_output["model_version"] = self.primary_model
            parsed_output["model_used"] = "primary"
            
            return parsed_output
            
        except Exception as e1:
            logger.warning(f"Primary model {self.primary_model} failed: {str(e1)}")
            logger.info(f"Attempting fallback to {self.fallback_model}")
            
            # Try fallback model (BioGPT)
            try:
                prompt = self._build_initial_prompt(
                    patient_context,
                    chief_complaint,
                    current_state,
                    last_session_summary,
                    files_count
                )
                
                response = self.client.text_generation(
                    prompt,
                    model=self.fallback_model,
                    max_new_tokens=1000,
                    temperature=0.7,
                    top_p=0.9,
                    repetition_penalty=1.1,
                )
                
                logger.info(f"SUCCESS: Fallback model {self.fallback_model} responded (length: {len(response)} chars)")
                
                # Parse the response
                parsed_output = self._parse_initial_response(response, patient_context, chief_complaint)
                
                processing_time = int(time.time() - start_time)
                parsed_output["processing_time_seconds"] = processing_time
                parsed_output["model_version"] = f"{self.fallback_model} (fallback)"
                parsed_output["model_used"] = "fallback"
                
                return parsed_output
                
            except Exception as e2:
                logger.error(f"Fallback model {self.fallback_model} also failed: {str(e2)}")
                # Both models failed - raise exception to mark VLM as failed
                raise Exception(f"All VLM models failed. Primary: {str(e1)}, Fallback: {str(e2)}")
    
    def process_doctor_query(
        self,
        patient_context: Dict[str, Any],
        session_context: Dict[str, Any],
        doctor_query: str,
        previous_chat: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate VLM response to doctor's question using MedGemma"""
        
        start_time = time.time()
        
        try:
            # Build conversational prompt
            prompt = self._build_chat_prompt(
                patient_context,
                session_context,
                doctor_query,
                previous_chat
            )
            
            logger.info(f"Sending doctor query to MedGemma")
            
            # Call Hugging Face Inference API (try primary first)
            try:
                response = self.client.text_generation(
                    prompt,
                    model=self.primary_model,
                    max_new_tokens=500,
                    temperature=0.7,
                    top_p=0.9,
                    repetition_penalty=1.1,
                )
            except Exception as e_primary:
                logger.warning(f"Primary model failed in chat: {str(e_primary)}, trying fallback")
                response = self.client.text_generation(
                    prompt,
                    model=self.fallback_model,
                    max_new_tokens=500,
                    temperature=0.7,
                    top_p=0.9,
                    repetition_penalty=1.1,
                )
            
            processing_time = int(time.time() - start_time)
            
            return {
                "findings": response.strip(),
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error in doctor query to MedGemma: {str(e)}")
            # Don't return fake response - raise exception
            raise Exception(f"VLM chat failed: {str(e)}")
    
    def _build_initial_prompt(
        self,
        patient_context: Dict,
        chief_complaint: str,
        current_state: str,
        last_session_summary: Optional[str],
        files_count: int
    ) -> str:
        """Build a structured medical prompt for initial session analysis"""
        
        age = patient_context.get("age", "unknown")
        sex = patient_context.get("sex", "unknown")
        chronic_diseases = patient_context.get("chronic_diseases", [])
        medications = patient_context.get("current_medications", [])
        
        prompt = f"""You are a medical AI assistant analyzing a patient case. Provide a structured medical analysis.

PATIENT INFORMATION:
- Age: {age} years
- Sex: {sex}
- Chronic Conditions: {', '.join(chronic_diseases) if chronic_diseases else 'None'}
- Current Medications: {', '.join(medications) if medications else 'None'}

PRESENTING COMPLAINT:
{chief_complaint}

CURRENT STATE:
{current_state}
"""
        
        if last_session_summary:
            prompt += f"\nPREVIOUS SESSION:\n{last_session_summary}\n"
        
        if files_count > 0:
            prompt += f"\nNOTE: {files_count} medical file(s) uploaded (X-rays, CT scans, or lab results).\n"
        
        prompt += """
Please provide a comprehensive medical analysis in the following format:

FINDINGS:
[Detailed clinical findings and assessment]

KEY OBSERVATIONS:
1. [First key observation]
2. [Second key observation]
3. [Third key observation]

TECHNICAL ASSESSMENT:
[Technical evaluation of available data]

SUGGESTED CONSIDERATIONS:
1. [First consideration]
2. [Second consideration]
3. [Third consideration]

DIFFERENTIAL PATTERNS:
1. [First differential diagnosis]
2. [Second differential diagnosis]
3. [Third differential diagnosis]
"""
        
        return prompt
    
    def _build_chat_prompt(
        self,
        patient_context: Dict,
        session_context: Dict,
        doctor_query: str,
        previous_chat: List[Dict]
    ) -> str:
        """Build a conversational prompt for doctor-VLM chat"""
        
        prompt = f"""You are a medical AI assistant in conversation with a doctor about a patient case.

PATIENT: {patient_context.get('age')} year old {patient_context.get('sex')}
CHIEF COMPLAINT: {session_context.get('chief_complaint', 'N/A')}
"""
        
        # Add previous chat context (last 3 exchanges)
        if previous_chat:
            prompt += "\nPREVIOUS CONVERSATION:\n"
            for msg in previous_chat[-6:]:  # Last 3 exchanges (doctor + vlm)
                sender = "Doctor" if msg.get("sender") == "doctor" else "AI"
                content = msg.get("content", "")
                prompt += f"{sender}: {content}\n"
        
        prompt += f"\nDoctor: {doctor_query}\n\nAI Assistant:"
        
        return prompt
    
    def _parse_initial_response(
        self,
        response: str,
        patient_context: Dict,
        chief_complaint: str
    ) -> Dict[str, Any]:
        """Parse MedGemma response into structured format"""
        
        # Initialize default structure
        parsed = {
            "findings": "",
            "key_observations": [],
            "technical_assessment": "",
            "suggested_considerations": [],
            "differential_patterns": []
        }
        
        # Try to extract sections
        sections = {
            "FINDINGS:": "findings",
            "KEY OBSERVATIONS:": "key_observations",
            "TECHNICAL ASSESSMENT:": "technical_assessment",
            "SUGGESTED CONSIDERATIONS:": "suggested_considerations",
            "DIFFERENTIAL PATTERNS:": "differential_patterns"
        }
        
        current_section = None
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check if this line is a section header
            for header, section_name in sections.items():
                if header in line.upper():
                    current_section = section_name
                    break
            else:
                # Add content to current section
                if current_section and line:
                    if current_section in ["key_observations", "suggested_considerations", "differential_patterns"]:
                        # Remove numbering and bullet points
                        cleaned = line.lstrip('0123456789.-•* ')
                        if cleaned:
                            parsed[current_section].append(cleaned)
                    else:
                        # Append to string fields
                        if parsed[current_section]:
                            parsed[current_section] += " " + line
                        else:
                            parsed[current_section] = line
        
        # Fallback: if parsing failed, use the whole response as findings
        if not parsed["findings"]:
            parsed["findings"] = response.strip()
        
        # Ensure we have at least some observations
        if not parsed["key_observations"]:
            parsed["key_observations"] = [
                f"Patient presenting with {chief_complaint.lower()}",
                f"Age {patient_context.get('age')} years - age-appropriate evaluation needed",
                "Comprehensive clinical assessment recommended"
            ]
        
        return parsed
    
# Singleton instance
medgemma_service = MedGemmaService()

