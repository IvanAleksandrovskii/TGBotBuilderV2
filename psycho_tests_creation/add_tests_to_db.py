# psycho_tests_creation/add_tests_to_db.py

from typing import List, Dict, Optional

import asyncio
from dataclasses import dataclass
import csv
import os
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Current file directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, project_root)

from core import log
from core.models import db_helper, Test, Question, Result


@dataclass(frozen=True)
class QuestionAnnotation:
    """Additional information for specific questions"""
    question_number: int  # Question number in CSV
    intro_text: Optional[str] = None
    comment: Optional[str] = None


@dataclass(frozen=True)
class TestData:
    name: str
    description: str
    is_multigraph: bool
    test_file: str
    interpretation_file: str
    
    same_answers: bool  
    same_answers_ordering: bool  
    same_answers_score: bool  
    
    category_names: Optional[Dict[str, str]] = None
    question_annotations: Optional[List[QuestionAnnotation]] = None


class TestProcessor:
    def __init__(self, test_data: TestData):
        self.test_data = test_data
        self.test_file_path = os.path.join(current_dir, test_data.test_file)
        
        self.annotations = {}
        if test_data.question_annotations:
            self.annotations = {
                ann.question_number: ann 
                for ann in test_data.question_annotations
            }

    def read_questions(self) -> List[Dict[str, any]]:
        """
        Reads questions from CSV file and processes them according to test settings
        Returns list of questions with their answers and scores
        """
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            question_column = next(h for h in headers if 'вопрос' in h.lower())
            score_columns = [h for h in headers if h != question_column]
            
            rows = list(reader)
            questions = []
            
            # If all questions have same answers, get them from first row
            answer_order = None
            if self.test_data.same_answers:
                first_row = rows[0]
                answer_order = [first_row[col].strip() for col in score_columns if first_row[col].strip()]

            for i, row in enumerate(rows, 1):  # Start from 1 to match question numbers
                # Get annotation for this question if exists
                annotation = self.annotations.get(i)
                
                question_dict = {
                    'text': row[question_column].strip(),
                    'order': i,
                    'answers': [],
                    'intro_text': annotation.intro_text if annotation else None,
                    'comment': annotation.comment if annotation else None
                }

                if self.test_data.same_answers_score:
                    # Use column headers as scores
                    answers = [(row[col].strip(), int(col)) for col in score_columns if row[col].strip()]
                else:
                    # Use sequential numbers as scores
                    answers = [(row[col].strip(), i) for i, col in enumerate(score_columns) if row[col].strip()]

                # Order answers if needed
                if self.test_data.same_answers_ordering and answer_order:
                    ordered_answers = []
                    for answer_text in answer_order:
                        matching_answer = next((a for a in answers if a[0] == answer_text), None)
                        if matching_answer:
                            ordered_answers.append(matching_answer)
                    question_dict['answers'] = ordered_answers
                else:
                    question_dict['answers'] = answers

                questions.append(question_dict)
            
            return questions

    def read_interpretation(self) -> List[Dict[str, any]]:
        """Reads test result interpretations from CSV file"""
        interpretation_file_path = os.path.join(current_dir, self.test_data.interpretation_file)
        results = []
        with open(interpretation_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                min_max_scores = row[0].split('-')
                results.append({
                    'min_score': int(min_max_scores[0]),
                    'max_score': int(min_max_scores[1]),
                    'text': row[1]
                })
        return results


async def create_test(session: AsyncSession, test_data: TestData) -> Test:
    """Creates or updates a psychological test with its questions and interpretations"""
    
    # Check if test exists
    existing_test = await session.execute(
        select(Test).where(Test.name == test_data.name)
    )
    existing_test = existing_test.scalar_one_or_none()
    
    if existing_test:
        log.info(f"Test {test_data.name} already exists, skipping")
        return existing_test

    # Create new test
    log.info(f"Creating test {test_data.name}")
    new_test = Test(
        name=test_data.name,
        description=test_data.description,
        is_psychological=True,
        multi_graph_results=test_data.is_multigraph,
        allow_back=True,
        allow_play_again=True,
        category_names=test_data.category_names if test_data.category_names else None
    )
    session.add(new_test)
    await session.flush()

    # Process questions
    processor = TestProcessor(test_data)
    questions = processor.read_questions()

    # Create questions with their answers
    for q_data in questions:
        question = Question(
            test_id=new_test.id,
            question_text=q_data['text'],
            order=q_data['order'],
            intro_text=q_data['intro_text'],
            comment=q_data['comment']
        )
        
        # Set answers and scores
        for i, (answer_text, score) in enumerate(q_data['answers'], start=1):
            setattr(question, f'answer{i}_text', answer_text)
            setattr(question, f'answer{i}_score', score)
        
        session.add(question)

    # Process interpretations
    interpretations = processor.read_interpretation()
    
    # Create interpretation results
    for interp in interpretations:
        result = Result(
            test_id=new_test.id,
            min_score=interp['min_score'],
            max_score=interp['max_score'],
            text=interp['text']
        )
        session.add(result)

    return new_test


# Example test data
anxiety = TestData(
    name="Шкала тревожности Бека",
    description="Отметьте, насколько вас беспокоил каждый из этих симптомов в течение последней недели, включая сегодняшний день.",
    is_multigraph=False,
    test_file="anxiety.csv",
    interpretation_file="anxiety_interpretation.csv",
    same_answers=True,
    same_answers_ordering=True,
    same_answers_score=True,
    
    # Example of adding annotations for specific questions
    question_annotations=[
        QuestionAnnotation(
            question_number=1,
            intro_text="Далее следуют вопросы об ощущении тревожности",
            comment="Это пояснение к первому вопросу"
        ),
    ]
    
)


hopeless = TestData(
    name="Шкала безнадёжности Бека",
    description="DESCRIPTION",
    is_multigraph=False,
    test_file="hopeless_bek.csv",
    interpretation_file="hopeless_bek_interpretation.csv",
    same_answers=True,
    same_answers_ordering=True,
    same_answers_score=False,
)


async def main():
    async for session in db_helper.session_getter():
        try:
            await create_test(session, anxiety)
            
            await create_test(session, hopeless)
            
            # TODO: Add other tests here
            
            await session.commit()
            log.info("Tests added successfully")
        except Exception as e:
            log.error(f"Error occurred: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(main())
