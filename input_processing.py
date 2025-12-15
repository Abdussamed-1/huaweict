"""
Input Processing Module
Handles speech-to-text conversion and pre-processing of user input.
Part of the Application Server (ECS) layer.
"""
import re
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class InputProcessor:
    """Processes and preprocesses user input before sending to the orchestrator."""
    
    def __init__(self):
        self.medical_keywords = [
            'symptom', 'pain', 'fever', 'headache', 'diagnosis', 'treatment',
            'patient', 'medical', 'disease', 'condition', 'illness', 'sick',
            'ache', 'nausea', 'dizziness', 'fatigue', 'cough', 'breath'
        ]
    
    def preprocess(self, user_input: str) -> Dict[str, Any]:
        """
        Preprocess user input: clean, normalize, and extract metadata.
        
        Args:
            user_input: Raw user input text
            
        Returns:
            Dictionary containing processed text and metadata
        """
        try:
            # Clean and normalize text
            cleaned_text = self._clean_text(user_input)
            
            # Extract medical context
            medical_context = self._extract_medical_context(cleaned_text)
            
            # Determine input type
            input_type = self._classify_input_type(cleaned_text)
            
            # Extract entities (basic)
            entities = self._extract_entities(cleaned_text)
            
            return {
                "original_text": user_input,
                "processed_text": cleaned_text,
                "medical_context": medical_context,
                "input_type": input_type,
                "entities": entities,
                "length": len(cleaned_text),
                "word_count": len(cleaned_text.split())
            }
        except Exception as e:
            logger.error(f"Error preprocessing input: {str(e)}")
            return {
                "original_text": user_input,
                "processed_text": user_input,
                "medical_context": {},
                "input_type": "unknown",
                "entities": [],
                "length": len(user_input),
                "word_count": len(user_input.split())
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep medical punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\-\:]', '', text)
        return text.strip()
    
    def _extract_medical_context(self, text: str) -> Dict[str, Any]:
        """Extract medical context from text."""
        text_lower = text.lower()
        
        # Check for medical keywords
        found_keywords = [kw for kw in self.medical_keywords if kw in text_lower]
        
        # Detect urgency indicators
        urgency_keywords = ['urgent', 'emergency', 'severe', 'critical', 'immediate']
        is_urgent = any(kw in text_lower for kw in urgency_keywords)
        
        # Detect question type
        is_question = text.strip().endswith('?')
        
        return {
            "medical_keywords": found_keywords,
            "is_urgent": is_urgent,
            "is_question": is_question,
            "has_medical_context": len(found_keywords) > 0
        }
    
    def _classify_input_type(self, text: str) -> str:
        """Classify the type of input."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['what', 'how', 'why', 'when', 'where', 'who']):
            return "question"
        elif any(word in text_lower for word in ['diagnose', 'diagnosis', 'what is', 'what are']):
            return "diagnostic_query"
        elif any(word in text_lower for word in ['treatment', 'treat', 'cure', 'medicine']):
            return "treatment_query"
        elif any(word in text_lower for word in ['symptom', 'symptoms', 'feeling', 'feel']):
            return "symptom_description"
        else:
            return "general"
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract basic entities from text (simplified version)."""
        entities = []
        
        # Extract potential medical terms (capitalized words)
        words = text.split()
        for word in words:
            if word[0].isupper() and len(word) > 3:
                entities.append(word)
        
        return entities
    
    def speech_to_text(self, audio_data: Optional[bytes] = None) -> str:
        """
        Convert speech to text (placeholder for future implementation).
        In production, this would integrate with Huawei Cloud ASR service.
        """
        # TODO: Integrate with Huawei Cloud ASR (Automatic Speech Recognition)
        # For now, return placeholder
        if audio_data:
            logger.warning("Speech-to-text not yet implemented. Audio data received but not processed.")
        return ""

