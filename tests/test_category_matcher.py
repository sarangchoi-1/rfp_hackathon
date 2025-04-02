"""
Category Matcher 테스트 모듈
의료/금융 카테고리 매칭 기능을 테스트합니다.
"""

import unittest
from unittest.mock import Mock, patch
import numpy as np
from ..agent.core.category_matcher import CategoryMatcher

class TestCategoryMatcher(unittest.TestCase):
    """CategoryMatcher 클래스의 테스트 케이스"""
    
    def setUp(self):
        """각 테스트 전에 실행되는 설정"""
        self.matcher = CategoryMatcher(confidence_threshold=0.5)
        
    def test_initialization(self):
        """초기화 테스트"""
        self.assertIsNotNone(self.matcher)
        self.assertEqual(self.matcher.confidence_threshold, 0.5)
        self.assertIn('medical', self.matcher.categories)
        self.assertIn('finance', self.matcher.categories)
        
    def test_medical_category_matching(self):
        """의료 카테고리 매칭 테스트"""
        task = {
            'description': '환자 진료 기록 시스템 구축',
            'task_type': 'development'
        }
        matches = self.matcher.match_task_to_categories(task)
        
        self.assertTrue(len(matches) > 0)
        medical_match = next((m for m in matches if m['category'] == 'medical'), None)
        self.assertIsNotNone(medical_match)
        self.assertGreater(medical_match['confidence'], 0.5)
        
    def test_finance_category_matching(self):
        """금융 카테고리 매칭 테스트"""
        task = {
            'description': '은행 대출 시스템 개선',
            'task_type': 'enhancement'
        }
        matches = self.matcher.match_task_to_categories(task)
        
        self.assertTrue(len(matches) > 0)
        finance_match = next((m for m in matches if m['category'] == 'finance'), None)
        self.assertIsNotNone(finance_match)
        self.assertGreater(finance_match['confidence'], 0.5)
        
    def test_keyword_matching(self):
        """키워드 매칭 테스트"""
        # 의료 키워드 테스트
        medical_score = self.matcher._calculate_keyword_score(
            '환자 진료 기록 시스템', 'medical'
        )
        self.assertGreater(medical_score, 0.5)
        
        # 금융 키워드 테스트
        finance_score = self.matcher._calculate_keyword_score(
            '은행 대출 시스템', 'finance'
        )
        self.assertGreater(finance_score, 0.5)
        
    def test_pattern_matching(self):
        """패턴 매칭 테스트"""
        # 의료 패턴 테스트
        medical_score = self.matcher._calculate_pattern_score(
            '의료시스템 구축', 'medical'
        )
        self.assertGreater(medical_score, 0.5)
        
        # 금융 패턴 테스트
        finance_score = self.matcher._calculate_pattern_score(
            '금융시스템 개선', 'finance'
        )
        self.assertGreater(finance_score, 0.5)
        
    @patch('agent.core.category_matcher.RAG_AVAILABLE', True)
    def test_rag_integration(self):
        """RAG 통합 테스트"""
        # RAG 관련성 계산 테스트
        rag_result = self.matcher._calculate_rag_relevance('의료 시스템')
        self.assertIsInstance(rag_result, dict)
        self.assertIn('score', rag_result)
        self.assertIn('doc_count', rag_result)
        
        # RAG 가중치 계산 테스트
        weight = self.matcher._get_rag_weight('medical', rag_result)
        self.assertIsInstance(weight, float)
        self.assertGreaterEqual(weight, 0.0)
        self.assertLessEqual(weight, 1.0)
        
    @patch('agent.core.category_matcher.RAG_AVAILABLE', False)
    def test_no_rag_fallback(self):
        """RAG 없을 때의 동작 테스트"""
        task = {
            'description': '의료 시스템 구축',
            'task_type': 'development'
        }
        matches = self.matcher.match_task_to_categories(task)
        
        self.assertTrue(len(matches) > 0)
        medical_match = next((m for m in matches if m['category'] == 'medical'), None)
        self.assertIsNotNone(medical_match)
        self.assertEqual(medical_match['rag_relevance'], 0.0)
        
    def test_invalid_task(self):
        """잘못된 작업 형식 테스트"""
        invalid_task = {
            'invalid_field': 'test'
        }
        
        with self.assertRaises(Exception):
            self.matcher.match_task_to_categories(invalid_task)
            
    def test_empty_task(self):
        """빈 작업 테스트"""
        empty_task = {
            'description': '',
            'task_type': ''
        }
        matches = self.matcher.match_task_to_categories(empty_task)
        self.assertEqual(len(matches), 0)
        
    def test_multilingual_support(self):
        """다국어 지원 테스트"""
        # 한글 테스트
        korean_task = {
            'description': '의료 시스템 구축',
            'task_type': '개발'
        }
        korean_matches = self.matcher.match_task_to_categories(korean_task)
        
        # 영어 테스트
        english_task = {
            'description': 'medical system development',
            'task_type': 'development'
        }
        english_matches = self.matcher.match_task_to_categories(english_task)
        
        self.assertTrue(len(korean_matches) > 0)
        self.assertTrue(len(english_matches) > 0)
        
    def test_relevance_calculation(self):
        """관련성 점수 계산 테스트"""
        # 의료 관련성 테스트
        medical_relevance = self.matcher.calculate_relevance(
            '환자 진료 기록', 'medical'
        )
        self.assertGreater(medical_relevance, 0.0)
        
        # 금융 관련성 테스트
        finance_relevance = self.matcher.calculate_relevance(
            '은행 대출', 'finance'
        )
        self.assertGreater(finance_relevance, 0.0)
        
    def test_category_score_calculation(self):
        """카테고리 점수 계산 테스트"""
        context = {'previous_task': '의료 시스템 구축'}
        
        # 의료 점수 테스트
        medical_score = self.matcher.calculate_category_score(
            '환자 진료 기록', 'medical', context
        )
        self.assertGreater(medical_score, 0.0)
        
        # 금융 점수 테스트
        finance_score = self.matcher.calculate_category_score(
            '은행 대출', 'finance', context
        )
        self.assertGreater(finance_score, 0.0)

if __name__ == '__main__':
    unittest.main() 