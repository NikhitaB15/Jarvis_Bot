import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

class KnowledgeManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.facts_file = self.data_dir / "personal_facts.json"
        self.conversations_file = self.data_dir / "conversations.json"
        self.patterns_file = self.data_dir / "learned_patterns.pkl"
        
        self.personal_facts = self._load_json(self.facts_file, {})
        self.conversations = self._load_json(self.conversations_file, [])
        self.learned_patterns = self._load_pickle(self.patterns_file, {})
    
    def _load_json(self, file_path: Path, default: Any) -> Any:
        """Load JSON file with default fallback"""
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
        return default
    
    def _load_pickle(self, file_path: Path, default: Any) -> Any:
        """Load pickle file with default fallback"""
        try:
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
        return default
    
    def _save_json(self, file_path: Path, data: Any):
        """Save data to JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving {file_path}: {e}")
    
    def _save_pickle(self, file_path: Path, data: Any):
        """Save data to pickle file"""
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Error saving {file_path}: {e}")
    
    def learn_fact(self, category: str, key: str, value: Any):
        """Learn a new personal fact"""
        if category not in self.personal_facts:
            self.personal_facts[category] = {}
        
        self.personal_facts[category][key] = {
            'value': value,
            'learned_at': datetime.now().isoformat(),
            'confidence': 1.0
        }
        self._save_json(self.facts_file, self.personal_facts)
    
    def get_fact(self, category: str, key: str = None) -> Optional[Any]:
        """Retrieve a personal fact"""
        if category in self.personal_facts:
            if key:
                fact = self.personal_facts[category].get(key)
                return fact['value'] if fact else None
            return self.personal_facts[category]
        return None
    
    def save_conversation(self, user_input: str, assistant_response: str, context: Dict = None):
        """Save conversation for learning"""
        conversation = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'assistant_response': assistant_response,
            'context': context or {}
        }
        
        self.conversations.append(conversation)
        
        # Keep only last 1000 conversations
        if len(self.conversations) > 1000:
            self.conversations = self.conversations[-1000:]
        
        self._save_json(self.conversations_file, self.conversations)
    
    def find_similar_conversations(self, query: str, limit: int = 5) -> List[Dict]:
        """Find similar past conversations"""
        # Simple keyword-based similarity (can be enhanced with NLP)
        query_words = set(query.lower().split())
        scored_conversations = []
        
        for conv in self.conversations[-100:]:  # Search last 100 conversations
            input_words = set(conv['user_input'].lower().split())
            similarity = len(query_words.intersection(input_words)) / len(query_words.union(input_words))
            
            if similarity > 0.1:  # Minimum similarity threshold
                scored_conversations.append((similarity, conv))
        
        # Sort by similarity and return top results
        scored_conversations.sort(key=lambda x: x[0], reverse=True)
        return [conv for _, conv in scored_conversations[:limit]]
    
    def learn_pattern(self, pattern_type: str, trigger: str, response: str):
        """Learn a new response pattern"""
        if pattern_type not in self.learned_patterns:
            self.learned_patterns[pattern_type] = {}
        
        self.learned_patterns[pattern_type][trigger] = {
            'response': response,
            'usage_count': 0,
            'last_used': None,
            'created_at': datetime.now().isoformat()
        }
        self._save_pickle(self.patterns_file, self.learned_patterns)
    
    def get_pattern_response(self, pattern_type: str, trigger: str) -> Optional[str]:
        """Get learned pattern response"""
        if pattern_type in self.learned_patterns and trigger in self.learned_patterns[pattern_type]:
            pattern = self.learned_patterns[pattern_type][trigger]
            
            # Update usage statistics
            pattern['usage_count'] += 1
            pattern['last_used'] = datetime.now().isoformat()
            self._save_pickle(self.patterns_file, self.learned_patterns)
            
            return pattern['response']
        return None
    
    def get_conversation_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get conversation summary for the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_conversations = [
            conv for conv in self.conversations
            if datetime.fromisoformat(conv['timestamp']) > cutoff_date
        ]
        
        return {
            'total_conversations': len(recent_conversations),
            'average_per_day': len(recent_conversations) / days,
            'most_common_topics': self._extract_topics(recent_conversations),
            'date_range': {
                'start': cutoff_date.isoformat(),
                'end': datetime.now().isoformat()
            }
        }
    
    def _extract_topics(self, conversations: List[Dict]) -> List[str]:
        """Extract common topics from conversations (simplified)"""
        # This is a basic implementation - could be enhanced with NLP
        word_freq = {}
        stop_words = {'the', 'is', 'are', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        
        for conv in conversations:
            words = conv['user_input'].lower().split()
            for word in words:
                if len(word) > 3 and word not in stop_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top 10 most frequent words
        return sorted(word_freq.keys(), key=word_freq.get, reverse=True)[:10]

