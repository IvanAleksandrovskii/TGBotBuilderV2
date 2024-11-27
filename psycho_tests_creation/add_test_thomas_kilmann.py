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
    name="Тест Томаса-Килманна, TKI",
    description=(
        "Этот тест исследует особенности установок, проявляющихся во время проведения различных переговоров. "
        "Это могут быть переговоры бытового, учебного, производственного характера."
        "\n\nК. Томас выделяет следующие способы регулирования конфликтов: "
        "\n1. противоборство, как стремление добиться удовлетворения своих интересов в ущерб другому;"
        "\n2. уступчивость, означающее в противоположность соперничеству, принесение в жертву собственных интересов ради другого;"
        "\n3. компромисс, как поиск средней позиции, то есть на отказ от некоторых своих интересов и признание интересов других;"
        "\n4. избегание, для которого характерно как отсутствие стремления к кооперации, так и отсутствие тенденции к достижению собственных целей;"
        "\n5. сотрудничество, когда участники ситуации приходят к альтернативе, полностью удовлетворяющей интересы обеих сторон."
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


# kilmann_test_result_1 = Result(
#     category_id = 0,
#     min_score=0,
#     max_score=0,
#     text="",
# )


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
