"""
MedGemma VLM Service - Connects to remote Colab instance
"""
import time
import requests
from typing import Dict, List, Any, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class MedGemmaService:
    """Real MedGemma VLM service - connects to remote Colab instance via HTTP"""
    
    def __init__(self):
        self.remote_url = settings.MEDGEMMA_REMOTE_URL
        self.model_version = "google/medgemma-1.5-4b-it"
        self.request_timeout = 120  # 2 minutes timeout for VLM processing
        logger.info(f"Initialized MedGemma service - Remote URL: {self.remote_url or 'NOT SET'}")
    
    def process_initial_session(
        self,
        patient_context: Dict[str, Any],
        chief_complaint: str,
        current_state: str,
        last_session_summary: Optional[str] = None,
        files_count: int = 0
    ) -> Dict[str, Any]:
        """Generate VLM initial output for a session by calling remote Colab instance"""
        
        if not self.remote_url:
            raise Exception("MEDGEMMA_REMOTE_URL not configured. Please set your Colab ngrok URL in environment variables.")
        
        start_time = time.time()
        
        try:
            # Construct medical prompt
            prompt = self._build_initial_prompt(
                patient_context,
                chief_complaint,
                current_state,
                last_session_summary,
                files_count
            )
            
            logger.info(f"Sending request to remote MedGemma service (prompt length: {len(prompt)} chars)")
            
            # Call remote Colab instance via HTTP
            response = requests.post(
                f"{self.remote_url}/predict_text",
                json={
                    "text": prompt,
                    "max_new_tokens": 1000
                },
                timeout=self.request_timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Remote service returned status {response.status_code}: {response.text}")
            
            response_data = response.json()
            model_response = response_data.get("response", "")
            
            logger.info(f"SUCCESS: Received response from remote MedGemma (length: {len(model_response)} chars)")
            
            # Parse the response into structured format
            parsed_output = self._parse_initial_response(model_response, patient_context, chief_complaint)
            
            processing_time = int(time.time() - start_time)
            parsed_output["processing_time_seconds"] = processing_time
            parsed_output["model_version"] = self.model_version
            
            return parsed_output
            
        except requests.exceptions.Timeout:
            logger.error("Remote MedGemma service timeout")
            raise Exception("Remote MedGemma service timeout - request took longer than 2 minutes")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to remote MedGemma service: {str(e)}")
            raise Exception(f"Cannot connect to remote MedGemma service. Is your Colab instance running? URL: {self.remote_url}")
        except Exception as e:
            logger.error(f"MedGemma processing failed: {str(e)}")
            raise Exception(f"MedGemma processing failed: {str(e)}")
    
    def process_reanalysis_with_context(
        self,
        patient_context: Dict[str, Any],
        chief_complaint: str,
        current_state: str,
        additional_context: str,
        original_vlm_output: Dict[str, Any],
        previous_chat: List[Dict[str, Any]],
        last_session_summary: Optional[str] = None,
        files_count: int = 0
    ) -> Dict[str, Any]:
        """Reanalyze session with additional doctor-provided context via remote Colab"""
        
        if not self.remote_url:
            raise Exception("MEDGEMMA_REMOTE_URL not configured. Please set your Colab ngrok URL in environment variables.")
        
        start_time = time.time()
        
        try:
            # Build enhanced prompt with original analysis and new context
            prompt = self._build_reanalysis_prompt(
                patient_context,
                chief_complaint,
                current_state,
                additional_context,
                original_vlm_output,
                previous_chat,
                last_session_summary,
                files_count
            )
            
            logger.info(f"Reanalyzing session with additional context (prompt length: {len(prompt)} chars)")
            
            # Call remote Colab instance
            response = requests.post(
                f"{self.remote_url}/predict_text",
                json={
                    "text": prompt,
                    "max_new_tokens": 1000
                },
                timeout=self.request_timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Remote service returned status {response.status_code}: {response.text}")
            
            response_data = response.json()
            model_response = response_data.get("response", "")
            
            logger.info(f"SUCCESS: Received reanalysis response (length: {len(model_response)} chars)")
            
            # Parse the response into structured format
            parsed_output = self._parse_initial_response(model_response, patient_context, chief_complaint)
            
            processing_time = int(time.time() - start_time)
            parsed_output["processing_time_seconds"] = processing_time
            parsed_output["model_version"] = f"{self.model_version} (reanalysis)"
            
            return parsed_output
            
        except Exception as e:
            logger.error(f"Error in reanalysis with context: {str(e)}")
            raise Exception(f"VLM reanalysis failed: {str(e)}")
    
    def process_doctor_query(
        self,
        patient_context: Dict[str, Any],
        session_context: Dict[str, Any],
        doctor_query: str,
        previous_chat: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate VLM response to doctor's question via remote Colab"""
        
        if not self.remote_url:
            raise Exception("MEDGEMMA_REMOTE_URL not configured. Please set your Colab ngrok URL in environment variables.")
        
        start_time = time.time()
        
        try:
            # Get additional contexts from session
            additional_contexts = session_context.get("additional_contexts", [])
            
            # Build conversational prompt
            prompt = self._build_chat_prompt(
                patient_context,
                session_context,
                doctor_query,
                previous_chat,
                additional_contexts
            )
            
            logger.info(f"Sending doctor query to remote MedGemma")
            
            # Call remote Colab instance
            response = requests.post(
                f"{self.remote_url}/predict_text",
                json={
                    "text": prompt,
                    "max_new_tokens": 500
                },
                timeout=self.request_timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Remote service returned status {response.status_code}: {response.text}")
            
            response_data = response.json()
            model_response = response_data.get("response", "")
            
            processing_time = int(time.time() - start_time)
            
            return {
                "findings": model_response.strip(),
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error in doctor query to MedGemma: {str(e)}")
            raise Exception(f"VLM chat failed: {str(e)}")
    
    def _build_reanalysis_prompt(
        self,
        patient_context: Dict,
        chief_complaint: str,
        current_state: str,
        additional_context: str,
        original_vlm_output: Dict,
        previous_chat: List[Dict],
        last_session_summary: Optional[str],
        files_count: int
    ) -> str:
        """Build a prompt for reanalysis with additional doctor-provided context"""
        
        age = patient_context.get("age", "unknown")
        sex = patient_context.get("sex", "unknown")
        chronic_diseases = patient_context.get("chronic_diseases", [])
        medications = patient_context.get("current_medications", [])
        
        prompt = f"""You are a medical AI assistant. A doctor has provided additional clinical context about this case that requires reanalysis.

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
        
        # Add original analysis
        prompt += f"""
ORIGINAL VLM ANALYSIS:
{original_vlm_output.get('findings', 'No previous findings available')}

KEY OBSERVATIONS FROM ORIGINAL ANALYSIS:
"""
        for obs in original_vlm_output.get('key_observations', []):
            prompt += f"- {obs}\n"
        
        # Add doctor's additional context
        prompt += f"""
ADDITIONAL CONTEXT FROM DOCTOR:
{additional_context}

"""
        
        # Add conversation history if any
        if previous_chat:
            prompt += "PREVIOUS CONVERSATION SUMMARY:\n"
            for msg in previous_chat[-4:]:  # Last 2 exchanges
                sender = "Doctor" if msg.get("sender") == "doctor" else "AI"
                content = msg.get("content", "")
                prompt += f"{sender}: {content[:200]}\n"  # Truncate long messages
        
        prompt += """
Please provide an UPDATED comprehensive medical analysis that INTEGRATES the new context with the original findings. Focus on how this new information changes or refines the assessment.

Provide your analysis in the following format:

FINDINGS:
[Updated clinical findings incorporating the new context]

KEY OBSERVATIONS:
1. [First key observation - updated or new]
2. [Second key observation - updated or new]
3. [Third key observation - updated or new]

TECHNICAL ASSESSMENT:
[Updated technical evaluation with new context]

SUGGESTED CONSIDERATIONS:
1. [First consideration - updated with new information]
2. [Second consideration - updated with new information]
3. [Third consideration - updated with new information]

DIFFERENTIAL PATTERNS:
1. [First differential diagnosis - updated]
2. [Second differential diagnosis - updated]
3. [Third differential diagnosis - updated]
"""
        
        return prompt
    
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
        previous_chat: List[Dict],
        additional_contexts: List[Dict] = []
    ) -> str:
        """Build a conversational prompt for doctor-VLM chat"""
        
        prompt = f"""You are a medical AI assistant in conversation with a doctor about a patient case.

PATIENT: {patient_context.get('age')} year old {patient_context.get('sex')}
CHIEF COMPLAINT: {session_context.get('chief_complaint', 'N/A')}
"""
        
        # Add additional contexts if any
        if additional_contexts:
            prompt += "\nADDITIONAL CLINICAL CONTEXT PROVIDED BY DOCTOR:\n"
            for ctx in additional_contexts:
                prompt += f"- {ctx.get('content', '')}\n"
        
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

