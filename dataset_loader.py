"""
Dataset Loader for Medical Q&A Dataset
Loads and processes the medical-o1-reasoning-SFT dataset from HuggingFace
"""
import logging
from typing import List, Dict, Optional
from datasets import load_dataset
import pandas as pd

logger = logging.getLogger(__name__)


class MedicalDatasetLoader:
    """Loads and processes medical Q&A dataset from HuggingFace."""
    
    def __init__(self, dataset_name: str = "FreedomIntelligence/medical-o1-reasoning-SFT"):
        """
        Initialize dataset loader.
        
        Args:
            dataset_name: HuggingFace dataset name
        """
        self.dataset_name = dataset_name
        self.dataset = None
        self.processed_data = []
    
    def load_dataset(self, split: str = "train", subset: Optional[str] = None):
        """
        Load dataset from HuggingFace.
        
        Args:
            split: Dataset split to load (train, validation, etc.)
            subset: Optional subset name (en, zh, etc.)
        """
        try:
            logger.info(f"Loading dataset: {self.dataset_name}")
            
            if subset:
                # Load specific subset (e.g., 'en' for English)
                self.dataset = load_dataset(
                    self.dataset_name,
                    subset,
                    split=split
                )
            else:
                # Load default dataset
                self.dataset = load_dataset(
                    self.dataset_name,
                    split=split
                )
            
            logger.info(f"Dataset loaded successfully. Size: {len(self.dataset)}")
            return self.dataset
        
        except Exception as e:
            logger.error(f"Error loading dataset: {str(e)}")
            raise
    
    def process_qa_pairs(self, max_samples: Optional[int] = None) -> List[Dict]:
        """
        Process dataset to extract question-response pairs.
        
        Args:
            max_samples: Maximum number of samples to process (None for all)
            
        Returns:
            List of dictionaries containing question, response, and metadata
        """
        if not self.dataset:
            raise ValueError("Dataset not loaded. Call load_dataset() first.")
        
        try:
            processed = []
            dataset_iter = self.dataset
            
            if max_samples:
                dataset_iter = self.dataset.select(range(min(max_samples, len(self.dataset))))
            
            logger.info(f"Processing {len(dataset_iter)} Q&A pairs...")
            
            for idx, item in enumerate(dataset_iter):
                try:
                    # Extract question and response
                    question = item.get("Question", "")
                    response = item.get("Response", "")
                    
                    # Skip if either is empty
                    if not question or not response:
                        continue
                    
                    # Create Q&A pair
                    qa_pair = {
                        "id": f"qa_{idx}",
                        "question": question,
                        "response": response,
                        "question_length": len(question),
                        "response_length": len(response),
                        "metadata": {
                            "dataset_index": idx,
                            "source": self.dataset_name
                        }
                    }
                    
                    # Add Complex_CoT if available (for future use)
                    if "Complex_CoT" in item:
                        qa_pair["reasoning_chain"] = item["Complex_CoT"]
                    
                    processed.append(qa_pair)
                    
                    if (idx + 1) % 1000 == 0:
                        logger.info(f"Processed {idx + 1} Q&A pairs...")
                
                except Exception as e:
                    logger.warning(f"Error processing item {idx}: {str(e)}")
                    continue
            
            self.processed_data = processed
            logger.info(f"Successfully processed {len(processed)} Q&A pairs")
            
            return processed
        
        except Exception as e:
            logger.error(f"Error processing Q&A pairs: {str(e)}")
            raise
    
    def get_statistics(self) -> Dict:
        """Get statistics about the processed dataset."""
        if not self.processed_data:
            return {}
        
        total_questions = len(self.processed_data)
        avg_question_length = sum(p["question_length"] for p in self.processed_data) / total_questions
        avg_response_length = sum(p["response_length"] for p in self.processed_data) / total_questions
        
        return {
            "total_pairs": total_questions,
            "average_question_length": avg_question_length,
            "average_response_length": avg_response_length,
            "min_question_length": min(p["question_length"] for p in self.processed_data),
            "max_question_length": max(p["question_length"] for p in self.processed_data),
            "min_response_length": min(p["response_length"] for p in self.processed_data),
            "max_response_length": max(p["response_length"] for p in self.processed_data)
        }
    
    def save_to_csv(self, filepath: str):
        """Save processed data to CSV file."""
        if not self.processed_data:
            raise ValueError("No processed data available. Call process_qa_pairs() first.")
        
        try:
            df = pd.DataFrame(self.processed_data)
            df.to_csv(filepath, index=False)
            logger.info(f"Saved {len(self.processed_data)} Q&A pairs to {filepath}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
            raise
    
    def get_sample(self, n: int = 5) -> List[Dict]:
        """Get sample Q&A pairs."""
        if not self.processed_data:
            return []
        
        return self.processed_data[:n]
