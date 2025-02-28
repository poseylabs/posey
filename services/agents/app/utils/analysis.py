from typing import Dict, Any, List
from app.models.schemas import Conversation, Message
from app.utils.embeddings import get_embeddings
import numpy as np
from sklearn.cluster import KMeans
from textblob import TextBlob

class ConversationAnalyzer:
    def __init__(self):
        self.embedding_model = "text-embedding-3-small"
    
    async def analyze_conversation(
        self, 
        conversation: Conversation, 
        messages: List[Message]
    ) -> Dict[str, Any]:
        """Analyze a conversation for insights"""
        
        # Get message embeddings
        message_texts = [msg.content for msg in messages]
        embeddings = await get_embeddings(message_texts, self.embedding_model)
        
        # Perform various analyses
        sentiment = await self._analyze_sentiment(messages)
        topics = await self._extract_topics(embeddings, messages)
        key_points = await self._extract_key_points(messages)
        
        return {
            "sentiment": sentiment,
            "topics": topics,
            "key_points": key_points,
            "metrics": {
                "message_count": len(messages),
                "avg_message_length": np.mean([len(msg.content) for msg in messages]),
                "user_engagement": self._calculate_engagement(messages)
            }
        }
    
    async def _analyze_sentiment(self, messages: List[Message]) -> Dict[str, float]:
        """Analyze sentiment of messages"""
        sentiments = []
        for msg in messages:
            blob = TextBlob(msg.content)
            sentiments.append(blob.sentiment.polarity)
        
        return {
            "overall": float(np.mean(sentiments)),
            "trend": self._calculate_sentiment_trend(sentiments)
        }
    
    async def _extract_topics(
        self, 
        embeddings: List[List[float]], 
        messages: List[Message]
    ) -> List[Dict[str, Any]]:
        """Extract main topics from conversation"""
        # Use clustering to identify topic groups
        n_clusters = min(5, len(messages))
        kmeans = KMeans(n_clusters=n_clusters)
        clusters = kmeans.fit_predict(embeddings)
        
        topics = []
        for i in range(n_clusters):
            cluster_msgs = [msg for j, msg in enumerate(messages) if clusters[j] == i]
            topic = self._summarize_cluster(cluster_msgs)
            topics.append(topic)
        
        return topics
    
    def _calculate_engagement(self, messages: List[Message]) -> float:
        """Calculate user engagement metrics"""
        # Implementation depends on your engagement criteria
        response_times = []
        for i in range(1, len(messages)):
            time_diff = messages[i].created_at - messages[i-1].created_at
            response_times.append(time_diff.total_seconds())
        
        if not response_times:
            return 0.0
            
        avg_response_time = np.mean(response_times)
        return 1.0 / (1.0 + avg_response_time/60.0)  # Normalize to 0-1 
