# psycho_tests_creation/add_test_thomas_kilmann.py


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


kilmann_test = Test(
    name="Стили поведения",
    description=(
        "Основано на тесте Томаса-Килманна. Используется для определения подхода кандидата к решению конфликтов и взаимодействию в команде."
    ),
    multi_graph_results=True,
    is_psychological=True,
    category_names={
        1: "Противоборство",
        2: "Сотрудничество",
        3: "Компромисс",
        4: "Избегание",
        5: "Уступчивость",
    },
)


result_resistance_1 = Result(
    category_id = 1,
    min_score=0,
    max_score=3,
    text=(
        "Недостаточное соперничество проявляется в "
        "нерешительности и низкой активности, самоустранении от решения проблем; склонности к обсуждению других, личным нападкам."
    ),
)


result_resistance_2 = Result(
    category_id = 1,
    min_score=4,
    max_score=8,
    text=(
        "Хорошо развиты способности использовать преимущества своей позиции, "
        "отстаиванать свое мнение и представление, а также фиксировать свою позицию и настаивать на ней."
    ),
)


result_resistance_3 = Result(
    category_id = 1,
    min_score=9,
    max_score=13,  # Should be 12, just to be sure all cases covered in case of mistake leaves 13 for now
    text=(
        "Чрезмерное соперничество ведет к потере обратной связи, снижению обучаемости. "
        "Проявляется в ошибках, отвлечении внимания, разговорах за спиной и периодической вспыльчивости."
    ),
)


result_cooperation_1 = Result(
    category_id = 2,
    min_score=0,
    max_score=3,
    text=(
        "Недостаточное владение сотрудничеством может привести к использованию быстрых шаблонных решений, бесправию, потере инновационности."
    ),
)


result_cooperation_2 = Result(
    category_id = 2,
    min_score=4,
    max_score=8,
    text=(
        "Хорошо развито восприятие ситуации без угрозы, эффективное слушание, "
        "аналитический подход к выявлению корневых причин проблем."
    )
)


result_cooperation_3 = Result(
    category_id = 2,
    min_score=9,
    max_score=13,  # Should be 12, just to be sure all cases covered in case of mistake leaves 13 for now
    text=(
        "Чрезмерное сотрудничество грозит затягиванием решения тривиальных "
        "вопросов, размыванием ответственности, риском быть используемым и перегрузкой работой."
    )
)


result_compromise_1 = Result(
    category_id=3,
    min_score=0,
    max_score=3,
    text=(
        "Недостаточное владение компромиссом ведет к конфронтации, постоянным конфликтам и неэффективным переговорам."
    )
)


result_compromise_2 = Result(
    category_id=3,
    min_score=4,
    max_score=8,
    text=(
        "Хорошо развиты коммуникативные навыки, умение поддерживать открытый диалог, "
        "находить взаимовыгодные решения, уступать и оценивать значимость всех аспектов проблемы."
    )
)


result_compromise_3 = Result(
    category_id=3,
    min_score=9,
    max_score=13,  # Should be 12, just to be sure all cases covered in case of mistake leaves 13 for now
    text=(
        "Чрезмерный компромисс ведет к потере стратегических целей, снижению доверия и цинизму. "
        "Уступки создают иллюзию благополучия, не решая сути конфликта."
    )
)


result_avoidance_1 = Result(
    category_id=4,
    min_score=0,
    max_score=3,
    text=(
        "Недостаточное использование избегания порождает враждебность и обиду. "
        "Работа становится подавляющей из-за неумения расставлять приоритеты и делегировать полномочия."
    )
)


result_avoidance_2 = Result(
    category_id=4,
    min_score=4,
    max_score=8,
    text=(
        "Хорошо развиты навыка прогнозирования выхода из конфликта, уклонения от вопросов, "
        "определения ситуаций для дипломатии, чувства времени и умения оставлять вопросы нерешёнными."
    )
)


result_avoidance_3 = Result(
    category_id=4,
    min_score=9,
    max_score=13,  # Should be 12, just to be sure all cases covered in case of mistake leaves 13 for now
    text=(
        "Чрезмерное избегание снижает вовлечённость: человек откладывает задачи, проявляет замкнутость, становится критичным и саркастичным."
    )
)


result_pliability_1 = Result(
    category_id=5,
    min_score=0,
    max_score=3,
    text=(
        "Слабое приспособление приводит к потере взаимопонимания, апатии, намёкам и двусмысленным "
        "высказываниям, что снижает моральные качества и мешает достижению результата."
    )
)


result_pliability_2 = Result(
    category_id=5,
    min_score=4,
    max_score=8,
    text=(
        "Хорошо развиты умения жертвовать, быть самоотверженным, подчиняться и уступать."
    )
)


result_pliability_3 = Result(
    category_id=5,
    min_score=9,
    max_score=13,  # Should be 12, just to be sure all cases covered in case of mistake leaves 13 for now
    text=(
        "Чрезмерное приспособление снижает влияние и вклад, ведёт к тревоге, страху перемен и стремлению сохранить всё неизменным."
    )
)


kilmann_question_1 = Question(
    order=1,
    intro_text=(
        "Вам будет предложен ряд пар утверждений, помеченных буквами А и В, из которых вы должны выбрать одно, более предпочитаемое, чем второе.\n\n"
        "Правильных или неправильных ответов здесь быть не может, поэтому не старайтесь долго их обдумывать – отвечайте, "
        "исходя из того, что больше соответствует вашим представлениям о самом себе."
    ),
    question_text=(
        "A) Иногда я предоставляю право решать проблему другим."
        "\n\nB) Я стараюсь подчеркнуть общее в наших позициях, а не обсуждать спорные моменты."
    ),
    answer1_text="A",
    answer1_score=4,
    answer2_text="B",
    answer2_score=5,
)

kilmann_question_2 = Question(
    order=2,
    question_text=(
        "A) Я пытаюсь найти компромиссное решение."
        "\n\nB) Я пытаюсь учесть все интересы: свои и оппонента"
    ),
    answer1_text="A",
    answer1_score=3,
    answer2_text="B",
    answer2_score=2,
)

kilmann_question_3 = Question(
    order=3,
    question_text=(
        "A) Обычно я твердо стою на своем."
        "\n\nB) Иногда я могу утешать других и пытаться сохранить с ними отношения."
    ),
    answer1_text="A",
    answer1_score=1,
    answer2_text="B",
    answer2_score=5,
)

kilmann_question_4 = Question(
    order=4,
    question_text=(
        "A) Я пытаюсь найти компромиссное решение."
        "\n\nB) Иногда я жертвую собственными интересами ради интересов противоположной стороны."
    ),
    answer1_text="A",
    answer1_score=3,
    answer2_text="B",
    answer2_score=5,
)

kilmann_question_5 = Question(
    order=5,
    question_text=(
        "A) При выработке решения ищу помощи со стороны других."
        "\n\nB) Я пытаюсь сделать все возможное, чтобы избежать ненужного обострения в отношениях."
    ),
    answer1_text="A",
    answer1_score=2,
    answer2_text="B",
    answer2_score=4,
)

kilmann_question_6 = Question(
    order=6,
    question_text=(
        "A) Я пытаюсь не создавать себе репутацию неприятного человека."
        "\n\nB) Я пытаюсь навязать другим свою позицию."
    ),
    answer1_text="A",
    answer1_score=4,
    answer2_text="B",
    answer2_score=1,
)

kilmann_question_7 = Question(
    order=7,
    question_text=(
        "A) Я пытаюсь отложить решение вопроса, чтобы иметь время тщательно его обдумать."
        "\n\nB) Я жертвую одними выгодами, чтобы получить взамен другие."
    ),
    answer1_text="A",
    answer1_score=4,
    answer2_text="B",
    answer2_score=3,
)

kilmann_question_8 = Question(
    order=8,
    question_text=(
        "A) Обычно я твердо настаиваю на своем."
        "\n\nB) Я пытаюсь сразу же открыто обсудить все интересы и спорные вопросы."
    ),
    answer1_text="A",
    answer1_score=1,
    answer2_text="B",
    answer2_score=2,
)

kilmann_question_9 = Question(
    order=9,
    question_text=(
        "A) Я чувствую, что различия в позициях не всегда стоят того, чтобы о них беспокоиться."
        "\n\nB) Я прилагаю некоторые усилия, чтобы повернуть дело на свой лад."
    ),
    answer1_text="A",
    answer1_score=4,
    answer2_text="B",
    answer2_score=1,
)

kilmann_question_10 = Question(
    order=10,
    question_text=(
        "A) Я твердо настаиваю на своем."
        "\n\nB) Я пытаюсь найти компромиссное решение."
    ),
    answer1_text="A",
    answer1_score=1,
    answer2_text="B",
    answer2_score=3,
)

kilmann_question_11 = Question(
    order=11,
    question_text=(
        "A) Я пытаюсь сразу же открыто обсудить все интересы и спорные вопросы."
        "\n\nB) Иногда я могу утешать других и пытаться сохранить с ними отношения."
    ),
    answer1_text="A",
    answer1_score=2,
    answer2_text="B",
    answer2_score=5,
)

kilmann_question_12 = Question(
    order=12,
    question_text=(
        "A) Иногда я избегаю занимать позицию, ведущую к конфронтации."
        "\n\nB) Я готов кое в чем уступить оппоненту, если он тоже мне уступит."
    ),
    answer1_text="A",
    answer1_score=4,
    answer2_text="B",
    answer2_score=3,
)

kilmann_question_13 = Question(
    order=13,
    question_text=(
        "A) Я предлагаю вариант «ни вам, ни нам»."
        "\n\nB) Я настаиваю на принятии моих условий."
    ),
    answer1_text="A",
    answer1_score=3,
    answer2_text="B",
    answer2_score=1,
)

kilmann_question_14 = Question(
    order=14,
    question_text=(
        "A) Я излагаю оппоненту мои соображения и интересуюсь его идеями."
        "\n\nB) Я пытаюсь продемонстрировать оппоненту логичность и выгоду принятия моих условий."
    ),
    answer1_text="A",
    answer1_score=2,
    answer2_text="B",
    answer2_score=1,
)

kilmann_question_15 = Question(
    order=15,
    question_text=(
        "A) Иногда я могу утешать других и пытаться сохранить с ними отношения."
        "\n\nB) Я пытаюсь сделать все возможное, чтобы избежать ненужного обострения в отношениях."
    ),
    answer1_text="A",
    answer1_score=5,
    answer2_text="B",
    answer2_score=4,
)

kilmann_question_16 = Question(
    order=16,
    question_text=(
        "A) Я стараюсь щадить чувства других."
        "\n\nB) Я пытаюсь убедить оппонента в выгодности принятия моих условий."
    ),
    answer1_text="A",
    answer1_score=5,
    answer2_text="B",
    answer2_score=1,
)

kilmann_question_17 = Question(
    order=17,
    question_text=(
        "A) Обычно я твердо настаиваю на своем."
        "\n\nB) Я пытаюсь сделать все возможное, чтобы избежать ненужного обострения в отношениях."
    ),
    answer1_text="A",
    answer1_score=1,
    answer2_text="B",
    answer2_score=4,
)

kilmann_question_18 = Question(
    order=18,
    question_text=(
        "A) Я позволяю оппоненту придерживаться своего мнения, если ему от этого лучше"
        "\n\nB) Я согласен кое в чем уступить оппоненту, если он тоже кое в чем мне уступит."
    ),
    answer1_text="A",
    answer1_score=5,
    answer2_text="B",
    answer2_score=3,
)

kilmann_question_19 = Question(
    order=19,
    question_text=(
        "A) Я пытаюсь сразу же, открыто, обсудить все интересы и спорные вопросы."
        "\n\nB) Я пытаюсь отложить принятие решения, чтобы иметь время тщательно его обдумать."
    ),
    answer1_text="A",
    answer1_score=2,
    answer2_text="B",
    answer2_score=4,
)

kilmann_question_20 = Question(
    order=20,
    question_text=(
        "A) Я пытаюсь сразу же обсудить противоречия."
        "\n\nB) Я пытаюсь найти справедливое сочетание из выгод и уступок для каждого из нас."
    ),
    answer1_text="A",
    answer1_score=2,
    answer2_text="B",
    answer2_score=3,
)

kilmann_question_21 = Question(
    order=21,
    question_text=(
        "A) При подготовке к переговорам я стараюсь учитывать интересы оппонента."
        "\n\nB) Я больше склонен к непосредственному и открытому обсуждению проблемы."
    ),
    answer1_text="A",
    answer1_score=5,
    answer2_text="B",
    answer2_score=2,
)

kilmann_question_22 = Question(
    order=22,
    question_text=(
        "A) Я стараюсь найти позицию, находящуюся между позицией оппонента и моей."
        "\n\nB) Я настаиваю на своих интересах."
    ),
    answer1_text="A",
    answer1_score=3,
    answer2_text="B",
    answer2_score=1,
)

kilmann_question_23 = Question(
    order=23,
    question_text=(
        "A) Очень часто я стараюсь удовлетворить все интересы, свои и оппонента."
        "\n\nB) Иногда я предоставляю право решать проблему другим."
    ),
    answer1_text="A",
    answer1_score=2,
    answer2_text="B",
    answer2_score=4,
)

kilmann_question_24 = Question(
    order=24,
    question_text=(
        "A) Я стараюсь пойти навстречу оппоненту, если его условия слишком для него много значат."
        "\n\nB) Я пытаюсь склонить оппонента к компромиссу."
    ),
    answer1_text="A",
    answer1_score=5,
    answer2_text="B",
    answer2_score=3,
)

kilmann_question_25 = Question(
    order=25,
    question_text=(
        "A) Я пытаюсь продемонстрировать оппоненту логичность и выгоду принятия моих условий."
        "\n\nB) При подготовке к переговорам я пытаюсь учитывать интересы оппонента."
    ),
    answer1_text="A",
    answer1_score=1,
    answer2_text="B",
    answer2_score=5,
)

kilmann_question_26 = Question(
    order=26,
    question_text=(
        "A) Я предлагаю вариант «ни вам, ни нам»."
        "\n\nB) Я почти всегда пытаюсь удовлетворить все пожелания, как свои, так и оппонента."
    ),
    answer1_text="A",
    answer1_score=3,
    answer2_text="B",
    answer2_score=2,
)

kilmann_question_27 = Question(
    order=27,
    question_text=(
        "A) Иногда я избегаю занимать позицию, ведущую к конфронтации."
        "\n\nB) Я позволяю оппоненту придерживаться своего мнения, если ему от этого лучше."
    ),
    answer1_text="A",
    answer1_score=4,
    answer2_text="B",
    answer2_score=5,
)

kilmann_question_28 = Question(
    order=28,
    question_text=(
        "A) Обычно я твердо стою на своем."
        "\n\nB) При выработке решения я постоянно ищу помощи со стороны других."
    ),
    answer1_text="A",
    answer1_score=1,
    answer2_text="B",
    answer2_score=2,
)

kilmann_question_29 = Question(
    order=29,
    question_text=(
        "A) Я предлагаю вариант «ни вам, ни нам»."
        "\n\nB) Я чувствую, что различия в позициях не всегда стоят того, чтобы о них беспокоиться."
    ),
    answer1_text="A",
    answer1_score=3,
    answer2_text="B",
    answer2_score=5,
)

kilmann_question_30 = Question(
    order=30,
    question_text=(
        "A) Я стараюсь щадить чувства других."
        "\n\nB) Я всегда стараюсь найти решение проблемы совместно с оппонентом."
    ),
    answer1_text="A",
    answer1_score=4,
    answer2_text="B",
    answer2_score=2,
)


kilman_test_results = [
    result_resistance_1, result_resistance_2, result_resistance_3,
    result_cooperation_1, result_cooperation_2, result_cooperation_3,
    result_compromise_1, result_compromise_2, result_compromise_3,
    result_avoidance_1, result_avoidance_2, result_avoidance_3,
    result_pliability_1, result_pliability_2, result_pliability_3,
]


kilman_test_questions = [
    kilmann_question_1, kilmann_question_2, kilmann_question_3, kilmann_question_4,
    kilmann_question_5, kilmann_question_6, kilmann_question_7, kilmann_question_8,
    kilmann_question_9, kilmann_question_10, kilmann_question_11, kilmann_question_12,
    kilmann_question_13, kilmann_question_14, kilmann_question_15, kilmann_question_16,
    kilmann_question_17, kilmann_question_18, kilmann_question_19, kilmann_question_20,
    kilmann_question_21, kilmann_question_22, kilmann_question_23, kilmann_question_24,
    kilmann_question_25, kilmann_question_26, kilmann_question_27, kilmann_question_28,
    kilmann_question_29, kilmann_question_30
]


async def add_kilmann_test(session: AsyncSession):
    try:
        is_exsisting = await session.execute(select(Test).where(Test.name == kilmann_test.name))
        is_exsisting = is_exsisting.scalar_one_or_none()
        
        if is_exsisting:
            log.info(f"Test {kilmann_test.name} already exists")
            return
        
        session.add(kilmann_test)
        await session.flush()
        
        for result in kilman_test_results:
            result.test_id = kilmann_test.id
            session.add(result)
        
        for question in kilman_test_questions:
            question.test_id = kilmann_test.id
            session.add(question)
        
        await session.commit()
        log.info(f"Test {kilmann_test.name} added")
        
    except Exception as e:
        log.error(f"Error while checking if test {kilmann_test.name} exists: {e}")


async def main():
    async with db_helper.db_session() as session:
        await add_kilmann_test(session)


if __name__ == "__main__":
    asyncio.run(main())
