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
from utils.logger import Logger
from utils.validators import Validator
from utils.exceptions import CategoryError
from ..memory.short_term import ShortTermMemory
from ..memory.long_term import LongTermMemory
from config.settings import Settings
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
import re
from functools import lru_cache

# RAG 파이프라인 임포트 시도 (없을 수 있음)
try:
    from rag_pipeline.vector_store import VectorStore
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    Logger(__name__).log_warning("RAG 파이프라인이 설치되지 않았습니다. 금융 데이터 관련 기능이 제한됩니다.")

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
        # 기본 유틸리티 초기화
        self.logger = Logger(__name__)  # 로그 기록을 위한 도구
        self.validator = Validator()    # 데이터 검증을 위한 도구
        self.settings = Settings()      # 설정값을 관리하는 도구
        
        # 메모리 시스템 초기화
        self.short_term_memory = ShortTermMemory()  # 최근 작업 내용을 저장하는 메모리
        self.long_term_memory = LongTermMemory()    # 과거 작업 결과를 저장하는 메모리
        
        # 설정값 초기화
        self.confidence_threshold = confidence_threshold  # 신뢰도 임계값
        
        # RAG 파이프라인 초기화 (가능한 경우에만)
        self.vector_store = None
        if RAG_AVAILABLE:
            try:
                self.vector_store = VectorStore()
                self.logger.log_info("RAG 파이프라인이 성공적으로 초기화되었습니다.")
            except Exception as e:
                self.logger.log_warning(f"RAG 파이프라인 초기화 실패: {str(e)}")
                RAG_AVAILABLE = False
        
        # 카테고리 정의 및 설정
        self.categories = {
            'medical': {
                'keywords': [
                    '의료', '환자', '진료', '병원', '처방', '약품', '검진',
                    '진단', '치료', '보건', '건강', '의약품', '의료기기',
                    'medical', 'healthcare', 'patient', 'treatment', 'diagnosis'
                ],
                'weight': 1.0,  # 의료 분야 기본 가중치
                'patterns': [
                    r'의료\w*', r'진료\w*', r'환자\w*', r'병원\w*',
                    r'처방\w*', r'진단\w*', r'치료\w*', r'보건\w*'
                ],
                'scoring_weights': {
                    'keyword': 0.4,
                    'pattern': 0.3,
                    'context': 0.2,
                    'history': 0.1,
                    'rag_relevance': 0.3 if RAG_AVAILABLE else 0.0
                }
            },
            'finance': {
                'keywords': [
                    '금융', '투자', '보험', '은행', '증권', '대출', '예금',
                    '신용', '금리', '주식', '펀드', '자산', '리스크', '규제',
                    'finance', 'banking', 'investment', 'insurance', 'risk'
                ],
                'weight': 1.0,  # 금융 분야 기본 가중치
                'patterns': [
                    r'금융\w*', r'투자\w*', r'보험\w*', r'은행\w*',
                    r'증권\w*', r'대출\w*', r'신용\w*', r'자산\w*'
                ],
                'scoring_weights': {
                    'keyword': 0.4,
                    'pattern': 0.3,
                    'context': 0.2,
                    'history': 0.1,
                    'rag_relevance': 0.3 if RAG_AVAILABLE else 0.0
                }
            }
        }
        
        # TF-IDF 벡터화기 초기화 및 캐싱
        self.vectorizer = TfidfVectorizer(
            max_features=1000,  # 최대 1000개의 단어를 고려
            stop_words=['의', '가', '이', '은', '들', '는', '좀', '잘', '걍', '과', '도', '를', '으로', '자', '에', '와', '한', '하다']  # 의미 없는 단어 제외
        )
        
        # 카테고리 벡터 미리 계산
        self._precompute_category_vectors()
        
        # RAG 관련 설정 추가
        self.rag_settings = {
            'min_relevance': 0.3,    # 최소 관련성 임계값
            'max_relevance': 0.8,    # 최대 관련성 임계값
            'weight_multiplier': 1.5, # RAG 관련성 가중치 승수
            'min_docs': 3,           # 최소 관련 문서 수
            'max_docs': 10,          # 최대 관련 문서 수
            'domain_boost': 1.3      # 도메인 부스트 계수
        }
        
        # 카테고리별 RAG 가중치 설정
        self.rag_weights = {
            'medical': {
                'base_weight': 0.5,      # 의료 도메인 기본 가중치
                'min_weight': 0.3,       # 최소 가중치
                'max_weight': 0.7,       # 최대 가중치
                'threshold': 0.5,        # 가중치 증가 임계값
                'domain_boost': True     # 도메인 부스트 적용
            },
            'finance': {
                'base_weight': 0.5,      # 금융 도메인 기본 가중치
                'min_weight': 0.3,       # 최소 가중치
                'max_weight': 0.7,       # 최대 가중치
                'threshold': 0.5,        # 가중치 증가 임계값
                'domain_boost': True     # 도메인 부스트 적용
            }
        }

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
        
        이 메서드는 TF-IDF와 코사인 유사도를 사용하여 텍스트 간의 관련성을 계산합니다.
        예를 들어:
        - "의료 시스템"과 "의료" 카테고리는 높은 관련성
        - "의료 시스템"과 "금융" 카테고리는 낮은 관련성
        
        Args:
            task_text (str): 작업 설명
            category (str): 카테고리 이름
            
        Returns:
            float: 0.0 ~ 1.0 사이의 관련성 점수
        """
        try:
            # 캐시된 카테고리 벡터 사용
            category_vector = self.category_vectors[category]
            
            # 작업 텍스트 벡터화
            task_vector = self.vectorizer.transform([task_text])
            
            # 코사인 유사도 계산
            similarity = cosine_similarity(task_vector, category_vector)[0][0]
            
            return float(similarity)
            
        except Exception as e:
            self.logger.log_error(f"관련성 점수 계산 중 오류 발생: {str(e)}")
            return 0.0

    def _calculate_keyword_score(self, text: str, category: str) -> float:
        """
        키워드 기반 점수 계산 (퍼지 매칭 추가)
        
        미리 정의된 키워드들이 텍스트에 얼마나 많이 포함되어 있는지 계산합니다.
        퍼지 매칭을 사용하여 유사한 단어도 인식합니다.
        """
        keywords = self.categories[category]['keywords']
        text = text.lower()
        matches = 0
        
        for keyword in keywords:
            # 정확한 매칭
            if keyword.lower() in text:
                matches += 1
            # 퍼지 매칭 (유사도 80% 이상)
            else:
                for word in text.split():
                    if fuzz.ratio(keyword.lower(), word) >= 80:
                        matches += 1
                        break
        
        return min(matches / len(keywords), 1.0)

    def _calculate_pattern_score(self, text: str, category: str) -> float:
        """
        패턴 매칭 점수 계산
        
        정규식 패턴이 텍스트에 얼마나 많이 매칭되는지 계산합니다.
        예: "의료시스템"은 "의료\w*" 패턴과 매칭됨
        """
        patterns = self.categories[category]['patterns']
        matches = sum(1 for pattern in patterns if re.search(pattern, text))
        return min(matches / len(patterns), 1.0)

    def _calculate_context_score(self, text: str, category: str, context: Dict) -> float:
        """
        컨텍스트 기반 점수 계산
        
        최근 작업 내용과의 관련성을 계산합니다.
        컨텍스트가 없는 경우 중간 점수(0.5)를 반환합니다.
        """
        if not context:
            return 0.5
            
        # 컨텍스트에서 관련 정보 추출
        context_text = ' '.join(str(v) for v in context.values())
        return self.calculate_relevance(text + ' ' + context_text, category)

    def _calculate_history_score(self, category: str) -> float:
        """
        과거 성과 기반 점수 계산
        
        이전에 비슷한 작업이 성공적으로 수행된 정도를 점수로 계산합니다.
        과거 데이터가 없는 경우 중간 점수(0.5)를 반환합니다.
        """
        try:
            history = self.long_term_memory.get_category_history(category)
            if not history:
                return 0.5
                
            success_rate = history.get('success_rate', 0.5)
            return float(success_rate)
            
        except Exception:
            return 0.5

    def _calculate_rag_relevance(self, text: str) -> Dict:
        """
        RAG 벡터 저장소를 사용한 관련성 점수 계산
        의료/금융 도메인 데이터에 대한 특별한 가중치 적용
        """
        if not RAG_AVAILABLE or not self.vector_store:
            return {
                'score': 0.0,
                'doc_count': 0,
                'avg_similarity': 0.0,
                'max_similarity': 0.0,
                'domain_match': False
            }
            
        try:
            # 관련 문서 검색
            relevant_docs = self.vector_store.search(
                text, 
                top_k=self.rag_settings['max_docs']
            )
            
            if not relevant_docs:
                return {
                    'score': 0.0,
                    'doc_count': 0,
                    'avg_similarity': 0.0,
                    'max_similarity': 0.0,
                    'domain_match': False
                }
            
            # 관련성 지표 계산
            similarities = [doc['similarity'] for doc in relevant_docs]
            doc_count = len(relevant_docs)
            avg_similarity = sum(similarities) / doc_count
            max_similarity = max(similarities)
            
            # 도메인 매칭 확인 (의료/금융 관련 문서 비율)
            domain_docs = sum(1 for doc in relevant_docs 
                            if any(domain in doc.get('category', '').lower() 
                                  for domain in ['medical', 'finance', '의료', '금융']))
            domain_match = domain_docs / doc_count > 0.5
            
            # 최종 점수 계산
            score = max_similarity
            
            # 도메인 매칭이 있는 경우 부스트 적용
            if domain_match:
                score *= self.rag_settings['domain_boost']
            
            # 문서 수에 따른 보너스
            if doc_count >= self.rag_settings['min_docs']:
                score *= (1 + (avg_similarity * 0.2))
            
            return {
                'score': min(max(score, self.rag_settings['min_relevance']), 
                           self.rag_settings['max_relevance']),
                'doc_count': doc_count,
                'avg_similarity': avg_similarity,
                'max_similarity': max_similarity,
                'domain_match': domain_match
            }
            
        except Exception as e:
            self.logger.log_warning(f"RAG 관련성 계산 중 오류 발생: {str(e)}")
            return {
                'score': 0.0,
                'doc_count': 0,
                'avg_similarity': 0.0,
                'max_similarity': 0.0,
                'domain_match': False
            }

    def _get_rag_weight(self, category: str, rag_relevance: Dict) -> float:
        """
        카테고리별 RAG 가중치를 동적으로 계산합니다.
        의료/금융 도메인에 대한 특별한 가중치 적용
        """
        if category not in self.rag_weights:
            return 0.0
            
        weights = self.rag_weights[category]
        base_weight = weights['base_weight']
        
        # 도메인 매칭이 있는 경우 추가 부스트
        if weights.get('domain_boost', False) and rag_relevance.get('domain_match', False):
            base_weight *= self.rag_settings['domain_boost']
        
        # 관련성 점수에 따른 가중치 조정
        if rag_relevance['score'] >= weights['threshold']:
            return min(base_weight * self.rag_settings['weight_multiplier'], 
                      weights['max_weight'])
        elif rag_relevance['score'] < weights['threshold'] / 2:
            return max(base_weight / self.rag_settings['weight_multiplier'], 
                      weights['min_weight'])
        else:
            return base_weight

    def calculate_category_score(self, task_text: str, category: str, context: Dict) -> float:
        """
        카테고리 매칭 신뢰도 점수 계산
        RAG 관련성은 동적 가중치로 적용됩니다.
        """
        try:
            scores = []
            weights = self.categories[category]['scoring_weights'].copy()
            
            # 기본 점수 계산
            keyword_score = self._calculate_keyword_score(task_text, category)
            pattern_score = self._calculate_pattern_score(task_text, category)
            context_score = self._calculate_context_score(task_text, category, context)
            history_score = self._calculate_history_score(category)
            
            scores.extend([keyword_score, pattern_score, context_score, history_score])
            
            # RAG 관련성 점수 추가 (가능한 경우에만)
            if RAG_AVAILABLE and category in self.rag_weights:
                rag_relevance = self._calculate_rag_relevance(task_text)
                rag_weight = self._get_rag_weight(category, rag_relevance)
                
                if rag_relevance['score'] > 0:
                    scores.append(rag_relevance['score'])
                    weights['rag_relevance'] = rag_weight
                    
                    # 로깅 추가
                    self.logger.log_info(
                        f"RAG 관련성 - 카테고리: {category}, "
                        f"점수: {rag_relevance['score']:.2f}, "
                        f"문서 수: {rag_relevance['doc_count']}, "
                        f"가중치: {rag_weight:.2f}"
                    )
            
            # 가중치 정규화
            total_weight = sum(weights.values())
            normalized_weights = {k: v/total_weight for k, v in weights.items()}
            
            # 가중 평균 계산
            final_score = np.average(scores, weights=list(normalized_weights.values()))
            
            return min(max(final_score, 0.0), 1.0)
            
        except Exception as e:
            self.logger.log_error(f"카테고리 점수 계산 중 오류 발생: {str(e)}")
            return 0.0

    def match_task_to_categories(self, task: Dict) -> List[Dict]:
        """
        작업을 관련 카테고리와 매칭하는 메인 메서드
        의료/금융 도메인에 특화된 매칭을 수행합니다.
        """
        try:
            if not self.validator.validate_task(task):
                raise CategoryError("유효하지 않은 작업 형식")

            context = self.short_term_memory.get_recent_context()
            matches = []
            task_text = f"{task['description']} {task.get('task_type', '')}"
            
            # 의료/금융 카테고리 매칭
            for category, config in self.categories.items():
                score = self.calculate_category_score(task_text, category, context)
                if score > self.confidence_threshold:
                    relevance = self.calculate_relevance(task_text, category)
                    rag_relevance = self._calculate_rag_relevance(task_text)
                    
                    match = {
                        'category': category,
                        'confidence': score,
                        'relevance_score': relevance,
                        'weighted_score': score * config['weight'],
                        'rag_relevance': rag_relevance['score'],
                        'rag_doc_count': rag_relevance['doc_count'],
                        'rag_avg_similarity': rag_relevance['avg_similarity']
                    }
                    matches.append(match)
            
            matches.sort(key=lambda x: x['weighted_score'], reverse=True)
            
            self.logger.log_info(f"작업을 {len(matches)}개의 카테고리와 매칭 (RAG 사용: {RAG_AVAILABLE})")
            return matches

        except Exception as e:
            self.logger.log_error(f"카테고리 매칭 중 오류 발생: {str(e)}")
            raise 