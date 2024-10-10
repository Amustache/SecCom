from typing import List, Optional
import re


from sqlalchemy import ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    @classmethod
    def get_attributes(cls):
        return [attr for attr in vars(cls) if not attr.startswith("_") and not attr[0].isupper()]


class Survey(Base):
    __tablename__ = "survey"

    uid: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    year: Mapped[int]

    questions: Mapped[List["QuestionPerSurvey"]] = relationship(back_populates="survey")

    @property
    def num_questions(self):
        return len(self.questions) or None

    def __lt__(self, other):
        return self.year < other.year

    def __repr__(self):
        return f"{self.name} ({self.year})"


class Canton(Base):
    __tablename__ = "canton"

    uid: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(unique=True)

    name_de: Mapped[str]
    name_fr: Mapped[str]
    name_it: Mapped[str]
    name_ro: Mapped[str]
    name_en: Mapped[str]

    districts: Mapped[List["District"]] = relationship(back_populates="canton")

    @property
    def num_districts(self):
        return len(self.districts)

    @property
    def num_communes(self):
        return sum(district.num_communes for district in self.districts)

    def __repr__(self):
        return f"{self.name} ({self.code})"


class District(Base):
    __tablename__ = "district"

    uid: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(unique=True)

    name_de: Mapped[str]
    name_fr: Mapped[str]
    name_it: Mapped[str]
    name_ro: Mapped[str]
    name_en: Mapped[str]

    canton_uid: Mapped[int] = mapped_column(ForeignKey("canton.uid"))
    canton: Mapped["Canton"] = relationship(back_populates="districts")

    communes: Mapped[List["Commune"]] = relationship(back_populates="district")

    @property
    def num_communes(self):
        return len(self.communes)

    def __repr__(self):
        return f"{self.name} ({self.code})"


class Commune(Base):
    __tablename__ = "commune"

    uid: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(unique=True)

    name_de: Mapped[str]
    name_fr: Mapped[str]
    name_it: Mapped[str]
    name_ro: Mapped[str]
    name_en: Mapped[str]

    district_uid: Mapped[int] = mapped_column(ForeignKey("district.uid"))
    district: Mapped["District"] = relationship(back_populates="communes")

    @property
    def canton(self):
        return self.district.canton

    answers: Mapped[List["Answer"]] = relationship(back_populates="commune")

    def __repr__(self):
        return f"{self.name} ({self.code})"


class QuestionCategory(Base):
    __tablename__ = "question_category"

    uid: Mapped[int] = mapped_column(primary_key=True)

    label: Mapped[str] = mapped_column(unique=True)

    # Optional
    text_de: Mapped[Optional[str]]
    text_fr: Mapped[Optional[str]]
    text_it: Mapped[Optional[str]]
    text_ro: Mapped[Optional[str]]
    text_en: Mapped[Optional[str]]

    options: Mapped[List["Option"]] = relationship(back_populates="question_category")

    questions_global: Mapped[List["QuestionGlobal"]] = relationship(back_populates="question_category")
    questions_per_survey: Mapped[List["QuestionPerSurvey"]] = relationship(back_populates="question_category")

    def __repr__(self):
        return f"{self.label} ({len(self.options)} option{'' if len(self.options) == 1 else 's'})"


class Option(Base):
    __tablename__ = "option"

    uid: Mapped[int] = mapped_column(primary_key=True)

    value: Mapped[str]

    question_category_uid: Mapped[int] = mapped_column(ForeignKey("question_category.uid"))
    question_category: Mapped["QuestionCategory"] = relationship(back_populates="options")

    # Optional
    _label: Mapped[Optional[str]]

    @hybrid_property
    def label(self):
        return self._label or self.value

    @label.setter
    def label(self, label):
        self._label = label

    text_de: Mapped[Optional[str]]
    text_fr: Mapped[Optional[str]]
    text_it: Mapped[Optional[str]]
    text_ro: Mapped[Optional[str]]
    text_en: Mapped[Optional[str]]

    answers: Mapped[List["Answer"]] = relationship(back_populates="option")

    def __repr__(self):
        return f"{self.label}"


class QuestionGlobal(Base):
    __tablename__ = "question_global"

    uid: Mapped[int] = mapped_column(primary_key=True)

    label: Mapped[str]

    # Optional
    question_category_uid: Mapped[Optional[int]] = mapped_column(ForeignKey("question_category.uid"))
    question_category: Mapped["QuestionCategory"] = relationship(back_populates="questions_global")

    text_de: Mapped[Optional[str]]
    text_fr: Mapped[Optional[str]]
    text_it: Mapped[Optional[str]]
    text_ro: Mapped[Optional[str]]
    text_en: Mapped[Optional[str]]

    questions_linked: Mapped[List["QuestionPerSurvey"]] = relationship(back_populates="question_global")

    @property
    def linked_surveys(self):
        return list(set([question.survey for question in self.questions_linked]))

    def __repr__(self):
        return f"Question Global #{self.uid}"


class QuestionPerSurvey(Base):
    __tablename__ = "question_per_survey"

    uid: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str] = mapped_column(unique=True)
    label: Mapped[str]

    # Optional
    question_category_uid: Mapped[Optional[int]] = mapped_column(ForeignKey("question_category.uid"))
    question_category: Mapped["QuestionCategory"] = relationship(back_populates="questions_per_survey")

    text_de: Mapped[Optional[str]]
    text_fr: Mapped[Optional[str]]
    text_it: Mapped[Optional[str]]
    text_ro: Mapped[Optional[str]]
    text_en: Mapped[Optional[str]]

    survey_uid: Mapped[int] = mapped_column(ForeignKey("survey.uid"))
    survey: Mapped["Survey"] = relationship(back_populates="questions")

    question_global_uid: Mapped[Optional[int]] = mapped_column(ForeignKey("question_global.uid"))
    question_global: Mapped["QuestionGlobal"] = relationship(back_populates="questions_linked")

    answers: Mapped[List["Answer"]] = relationship(back_populates="question")

    @property
    def num_answers(self):
        return len(self.answers) or None

    def __lt__(self, other):
        study_name_left, question_left = self.code.split("_", 1)
        study_name_right, question_right = other.code.split("_", 1)

        if study_name_left != study_name_right:
            return self.survey < other.survey

        if question_left == question_right:
            return False

        question_left = question_left.split("_")
        question_right = question_right.split("_")

        for l, r in zip(question_left, question_right):
            if l == r:
                continue

            if l is None:
                return True
            if r is None:
                return False

            l_re = re.split(r"(\d+)", l)
            r_re = re.split(r"(\d+)", r)
            for l2, r2 in zip(l_re, r_re):
                if l2 == r2:
                    continue

                if l2 is None:
                    return True
                if r2 is None:
                    return False

                if l2.isdigit() and r2.isdigit():
                    return int(l2) < int(r2)
                else:
                    return l2 < r2

    def __repr__(self):
        return f"Question #{self.code} from survey #{self.survey_uid}"


class Answer(Base):
    __tablename__ = "answer"

    uid: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int]

    question_uid: Mapped[int] = mapped_column(ForeignKey("question_per_survey.uid"))
    question: Mapped["QuestionPerSurvey"] = relationship(back_populates="answers")

    commune_uid: Mapped[int] = mapped_column(ForeignKey("commune.uid"))
    commune: Mapped["Commune"] = relationship(back_populates="answers")

    # Optional, either one or the other
    option_uid: Mapped[Optional[int]] = mapped_column(ForeignKey("option.uid"))
    option: Mapped["Option"] = relationship(back_populates="answers")

    _value: Mapped[Optional[str]]

    @hybrid_property
    def value(self):
        return self._value or self.option.value

    @value.setter
    def value(self, value):
        self._value = value

    def __repr__(self):
        return f"Answer from commune #{self.commune.code} to question #{self.question.code}"
