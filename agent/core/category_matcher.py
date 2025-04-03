"""
카테고리 매칭 모듈 (Category Matcher Module)
작업을 관련 문서 카테고리와 매칭하여 정보 검색을 지원합니다.

이 모듈은 RFP(제안요청서)의 내용을 분석하여 다음과 같은 작업을 수행합니다:
1. 입력된 텍스트를 여러 카테고리로 분류
2. 각 카테고리와의 관련성을 점수로 계산
3. 가장 적합한 카테고리를 찾아 제시
4. 금융 데이터베이스와의 연관성 확인 (RAG 파이프라인 사용 가능 시)

예시:
입력: "의료 정보 시스템 보안 강화 프로젝트"
출력: [
    {'category': 'medical', 'confidence': 0.8, 'rag_relevance': 0.3, ...},
    {'category': 'technology', 'confidence': 0.7, 'rag_relevance': 0.4, ...},
    {'category': 'compliance', 'confidence': 0.6, 'rag_relevance': 0.5, ...}
]
"""

from typing import List, Dict, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

class CategoryMatcher:
    """
    카테고리 매칭기 클래스
    작업을 관련 문서 카테고리와 매칭하고 신뢰도 점수를 계산합니다.

    주요 기능:
    1. 텍스트 분석: 입력된 텍스트에서 중요한 단어와 패턴을 찾습니다.
    2. 카테고리 매칭: 찾은 단어와 패턴을 미리 정의된 카테고리와 비교합니다.
    3. 점수 계산: 각 카테고리와의 관련성을 점수로 계산합니다.
    4. 결과 정렬: 가장 관련성 높은 카테고리 순으로 결과를 정렬합니다.
    """
    
    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        
        # 카테고리 정의
        self.categories = {
            'finance': {
                'keywords': [
                    '금융', '투자', '보험', '은행', '증권', '대출', '예금',
                    '신용', '금리', '주식', '펀드', '자산', '리스크', '규제',
                    'finance', 'banking', 'investment', 'insurance', 'risk'
                ],
                'weight': 1.0,
                'patterns': [
                    r'금융\w*', r'투자\w*', r'보험\w*', r'은행\w*',
                    r'증권\w*', r'대출\w*', r'신용\w*', r'자산\w*'
                ]
            }
        }
        
        # TF-IDF 벡터화기 초기화
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=['의', '가', '이', '은', '들', '는', '좀', '잘', '걍', '과', '도', '를', '으로', '자', '에', '와', '한', '하다']
        )
        
        # 카테고리 벡터 미리 계산
        self._precompute_category_vectors()

    def _precompute_category_vectors(self):
        """카테고리 벡터를 미리 계산하여 캐시"""
        self.category_vectors = {}
        for category, config in self.categories.items():
            category_text = ' '.join(config['keywords'])
            vector = self.vectorizer.fit_transform([category_text])
            self.category_vectors[category] = vector

    @lru_cache(maxsize=1000)
    def calculate_relevance(self, task_text: str, category: str) -> float:
        """
        작업과 카테고리 간의 관련성 점수 계산 (캐시 적용)
        """
        try:
            category_vector = self.category_vectors[category]
            task_vector = self.vectorizer.transform([task_text])
            similarity = cosine_similarity(task_vector, category_vector)[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"관련성 점수 계산 중 오류 발생: {str(e)}")
            return 0.0

    def _calculate_keyword_score(self, text: str, category: str) -> float:
        """키워드 기반 점수 계산"""
        keywords = self.categories[category]['keywords']
        text = text.lower()
        matches = sum(1 for keyword in keywords if keyword.lower() in text)
        return min(matches / len(keywords), 1.0)

    def _calculate_pattern_score(self, text: str, category: str) -> float:
        """패턴 매칭 점수 계산"""
        patterns = self.categories[category]['patterns']
        matches = sum(1 for pattern in patterns if re.search(pattern, text))
        return min(matches / len(patterns), 1.0)

    def calculate_category_score(self, task_text: str, category: str) -> float:
        """카테고리 매칭 신뢰도 점수 계산"""
        try:
            # 기본 점수 계산
            keyword_score = self._calculate_keyword_score(task_text, category)
            pattern_score = self._calculate_pattern_score(task_text, category)
            relevance_score = self.calculate_relevance(task_text, category)
            
            # 가중 평균 계산 (키워드: 0.4, 패턴: 0.3, 관련성: 0.3)
            final_score = (keyword_score * 0.4 + pattern_score * 0.3 + relevance_score * 0.3)
            
            return min(max(final_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"카테고리 점수 계산 중 오류 발생: {str(e)}")
            return 0.0

    def match_task_to_categories(self, task: Dict) -> List[Dict]:
        """작업을 관련 카테고리와 매칭하는 메인 메서드 
        Args:
            task (Dict): 작업 정보 project_info
        Returns:
            List[Dict]: 정렬된된매칭된 카테고리 정보
        """
        try:
            matches = []
            task_text = task.get('description', '')
            
            for category, config in self.categories.items():
                score = self.calculate_category_score(task_text, category)
                if score > self.confidence_threshold:
                    match = {
                        'category_id': category,
                        'score': score,
                        'name': category,
                        'weighted_score': score * config['weight']
                    }
                    matches.append(match)
            
            matches.sort(key=lambda x: x['weighted_score'], reverse=True)
            logger.info(f"작업을 {len(matches)}개의 카테고리와 매칭")
            return matches

        except Exception as e:
            logger.error(f"카테고리 매칭 중 오류 발생: {str(e)}")
            return [] 