# psycho_tests_creation/add_test_critical_thinking.py

import sys
import os

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Current file directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, project_root)

from core import log
from core.models import db_helper
from core.models.quiz import Test, Question, Result


# Critical Thinking Test Starkey
critical_thinking = Test(
    name="Тест критического мышления Старки",
    description=(
        "Тест критического мышления Старки был опубликован в книге Лорен Старки «Навыки критического мышления за 20 минут в день», "
        "этот тест служит эффективным инструментом для первичной оценки способности человека к аналитическому и логическому мышлению."
    ),
    multi_graph_results=False,
    is_psychological=True,
)


critical_thinking_result_1 = Result(
    min_score=0,
    max_score=6,
    text=(
        "Низкие результаты теста указывают на слабое критическое мышление: человек справляется лишь с 10-20% заданий. "
        "Это проявляется в неспособности логически мыслить, отфильтровывать недостоверную информацию и принимать взвешенные решения. "
        "Такой индивид склонен к эзотерическим учениям, может попадать в секты или примыкать к радикальным идеологиям. "
        "Он легко подвергается манипуляциям, не осознает собственных ошибок и предпочитает следовать инстинктам и традициям. "
        "Для улучшения ситуации рекомендуется развивать критическое мышление через образовательные программы и литературу, "
        "что поможет оптимизировать стратегии адаптации и улучшить качество жизни."
    ),
)


critical_thinking_result_2 = Result(
    min_score=7,
    max_score=21,
    text=(
        "Средние результаты теста говорят о том, что у субъекту доступны большинство операций критического мышления: "
        "логика, процессы индукции и дедукции, способность отфильтровывать недостоверную информацию и собирать объективную, "
        "выявлять манипуляции, иллюзии и ложные идеи, принимать взвешенные решения, аргументированно дискутировать, осознавать "
        "свои предвзятости и необъективность других. Однако в сложных ситуациях или при столкновении с чем-то, что не вписывается "
        "в его картину мира, возможны ошибки в логических решениях, аргументации. В таких случаях субъект может чувствовать себя недостаточно "
        "компетентным, проявлять агрессию в спорах ил приводить не достаточно корректные аргументы. в таких случаях субъекту рекомендовано заниматься "
        "самообразованием, саморазвитием, увеличением информированности по необходимым вопросам."
    ),
)


critical_thinking_result_3 = Result(
    min_score=22,
    max_score=27,
    text=(
        "Очень высокие результаты по тесту свидетельствуют о том, что у данного индивида развиты практически все операции критического мышления "
        "– логика, индукция, дедукция, рефлексия, контроль над эмоциями, искажающими принятие решений, анализ информации на достоверность, способность "
        "распознавать свои иллюзии, манипуляции со стороны окружающих, рекламы, пропаганды, способность отделять оценки и допущения от фактов, обнаруживать "
        "причинно-следственные связи или принимать их отсутствие, признавать ограниченность собственных мыслительных процессов, вырабатывать наиболее "
        "оптимальные решения в условиях неопределенности и риска, умение ставить реалистичные цели и находить адекватные пути их достижения. "
        "Такой человек является эффективным профессионалом во всех видах работы, требующей принятия сложных и ответственных решений, а также имеет "
        "общее преимущество в жизнедеятельности, адаптации к меняющимся условиям среды."
    ),
)


critical_thinking_question_1 = Question(
    order=1,
    intro_text=(
        "Инструкция:\n\n"
        "Во всех задачах (кроме первой) выберите и отметьте один наиболее правильный (подходящий) вариант."
        "В первой задаче отметьте наименее правильный (подходящий) вариант ответа."
    ),
    question_text=(
        "Вы провели успешный поиск работы, и теперь у вас есть три различных предложения на выбор. "
        "Что можно сделать, чтобы наиболее тщательно изучить потенциальных работодателей?"
        "\n\nA)Исследовать их вебсайты."
        "\nB) Посмотреть новости, чтобы выяснить, упоминаются ли в них данные компании."
        "\nC) Исследовать их финансовое положение."
        "\nD) Поговорить с людьми, которые уже там работают."
    ),
    
    answer1_text="A",
    answer1_score=0,
    
    answer2_text="B",
    answer2_score=1,
    
    answer3_text="C",
    answer3_score=0,
    
    answer4_text="D",
    answer4_score=0,
)


critical_thinking_question_2 = Question(
    order=2,
    text=(
        "Какой вывод является наилучшим для суждения, начинающегося словами: «восемь человек в моём классе…»?"
        "\n\nA) любят тефтели, значит, и мне следует их любить.",
        "\nB) живут в южной части города, поэтому я тоже должен там жить.",
        "\nC) из тех, кто готовился по конспекту Андрея, получили «удовлетворительно», поэтому я получу такую же оценку.",
        "\nD) из тех, кто уже познакомился с новым директором школы, ему симпатизируют, поэтому мне он тоже понравится.",
    ),
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=1,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_3 = Question(
    order=3,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_4 = Question(
    order=4,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_5 = Question(
    order=5,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_6 = Question(
    order=6,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_7 = Question(
    order=7,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_8 = Question(
    order=8,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_9 = Question(
    order=9,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_10 = Question(
    order=10,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_11 = Question(
    order=11,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_12 = Question(
    order=12,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_13 = Question(
    order=13,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_14 = Question(
    order=14,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_15 = Question(
    order=15,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_16 = Question(
    order=16,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_17 = Question(
    order=17,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_18 = Question(
    order=18,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_19 = Question(
    order=19,
    intro_text=(
        "Прочитайте текст и ответьте на два последующих вопроса. "
        "\n\n«Я всегда знала, что хочу стать морским биологом. В шесть лет мои родители повели меня в аквариум, и это меня зацепило. "
        "А в колледже я получила практику на океанском исследовательском рейсе и решила специализироваться в океанографии. "
        "Поездка спонсировалась Службой Исследования Планктона, и нашей целью было собрать как можно больше различных типов микроскопических "
        "растений и животных, чтобы посмотреть, влияет ли на морскую экосистему увеличение количества рыбаков. Наша группа была разделена на "
        "две команды для сбора различных видов планктона. Работать с фитопланктоном, особенно с сине-зелеными водорослями, было здорово. "
        "Мы измеряли уровень хлорофилла в воде, чтобы определить, где и в каких количествах есть фитопланктон. Работалось хорошо, так как вода "
        "была прозрачной, без мути и грязи»."
    ),
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_20 = Question(
    order=20,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_21 = Question(
    order=21,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_22 = Question(
    order=22,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_23 = Question(
    order=23,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_24 = Question(
    order=24,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_25 = Question(
    order=25,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_26 = Question(
    order=26,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)

critical_thinking_question_27 = Question(
    order=27,
    text="",
    answer1_text="A",
    answer1_score=0,
    answer2_text="B",
    answer2_score=0,
    answer3_text="C",
    answer3_score=0,
    answer4_text="D",
    answer4_score=0,
)


async def add_critical_thinking_test(session: AsyncSession):
    try:
        is_existing = await session.execute(select(Test).where(Test.name == critical_thinking.name))
        is_existing = is_existing.scalar_one_or_none()
        if is_existing:
            log.info("Test already exists, skipping")
            return
        
        session.add(critical_thinking)
        
        await session.flush()

        critical_thinking_results = [
            critical_thinking_result_1,
            critical_thinking_result_2,
            critical_thinking_result_3,
        ]
        
        for result in critical_thinking_results:
            result.test_id = critical_thinking.id
            session.add(result)

        critical_thinking_questions = [
            critical_thinking_question_1,
        ]
        
        for question in critical_thinking_questions:
            question.test_id = critical_thinking.id
            session.add(question)
        
        for result in critical_thinking_results:
            session.add(result)
            
        for question in critical_thinking_questions:
            session.add(question)
        
        await session.commit()
        
        log.info("Critical thinking test added successfully")
        
    except Exception as e:
        log.error(f"Failed to add critical thinking test: {e}")


async def main():
    async with db_helper.db_session() as session:
        await add_critical_thinking_test(session)


if __name__ == "__main__":
    asyncio.run(main())
