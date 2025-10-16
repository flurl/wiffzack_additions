from dataclasses import dataclass
from datetime import datetime
from typing import LiteralString, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from wiffzack.db_connection import DatabaseConnection
    from wiffzack.types import DBResult


@dataclass
class ChecklistMaster:
    id: int
    name: str
    category: str


@dataclass
class ChecklistQuestion:
    id: int
    text: str
    order: int
    master_id: int  # Foreign key to ChecklistMaster.chm_id


@dataclass
class Checklist:
    id: int
    datum: datetime
    completed: bool
    master_name: str


@dataclass
class ChecklistAnswer:
    id: int
    checklist_id: int  # Foreign key to Checklist.chk_id
    question_text: str  # Foreign key to ChecklistQuestion.chq_id
    choice: Optional[bool]  # NULL in SQL, so Optional in Python


def create_checklist_from_master(db: "DatabaseConnection", master_id: int) -> Checklist:
    query: LiteralString = """
        insert into checklists (chk_datum, chk_completed, chk_master_name)
        OUTPUT INSERTED.chk_id, INSERTED.chk_datum, INSERTED.chk_completed, INSERTED.chk_master_name
        select getutcdate(), 0, chm_name
        from checklist_master
        where chm_id = %s
    """
    result: DBResult = db.execute_query(query, (master_id,))
    if not result:
        raise RuntimeError("Failed to create checklist from master.")
    checklist: Checklist = Checklist(
        id=result[0][0], datum=result[0][1], completed=result[0][2], master_name=result[0][3])
    # if the checklist was successfully created, insert the answers
    query = """
        insert into checklist_answers (cha_chkid, cha_question_text, cha_choice, cha_order)
        OUTPUT INSERTED.cha_id, INSERTED.cha_chkid, INSERTED.cha_question_text, INSERTED.cha_choice, INSERTED.cha_order
        select %s, chq_text, null, chq_order
        from checklist_questions
        where chq_chmid = %s"""
    result = db.execute_query(query, (checklist.id, master_id,))
    if not result:
        raise RuntimeError("Failed to create checklist answers.")
    db.commit()
    return checklist


def get_latest_checklist(db: "DatabaseConnection", master_id: int) -> Optional[Checklist]:
    query: LiteralString = """
        select top 1 chk_id, chk_datum, chk_completed, chk_master_name
        from checklists
        where chk_master_name = (select chm_name from checklist_master where chm_id = %s)
        and chk_completed = 0
        order by chk_datum desc
    """
    result: DBResult = db.execute_query(query, (master_id,))
    if not result:
        return None
    return Checklist(id=result[0][0], datum=result[0][1], completed=result[0][2], master_name=result[0][3])


def close_checklist(db: "DatabaseConnection", checklist_id: int) -> None:
    query: LiteralString = """
        update checklists
        set chk_completed = 1
        output inserted.chk_id
        where chk_id = %s
    """
    result: DBResult = db.execute_query(query, (checklist_id,))
    if not result or not result[0][0] == checklist_id:
        raise RuntimeError(
            f"Failed to close checklist with id {checklist_id}.")
    db.commit()


# region ChecklistMaster CRUD
def create_checklist_master(db: "DatabaseConnection", name: str, category: str) -> ChecklistMaster:
    """Creates a new checklist master and returns it."""
    name = name.strip()
    if not name:
        raise ValueError("Checklist master name cannot be empty.")
    category = category.strip()
    if not category:
        raise ValueError("Checklist master category cannot be empty.")
    query = "INSERT INTO checklist_master (chm_name, chm_category) OUTPUT INSERTED.chm_id, INSERTED.chm_name, INSERTED.chm_category VALUES (%s, %s)"
    result: DBResult = db.execute_query(query, (name, category))
    if not result:
        raise RuntimeError("Failed to create checklist master.")
    db.commit()
    chm_id, chm_name, chm_category = result[0]
    return ChecklistMaster(id=chm_id, name=chm_name, category=chm_category)


def get_checklist_master(db: "DatabaseConnection", master_id: int) -> Optional[ChecklistMaster]:
    """Retrieves a single checklist master by its ID."""
    query = "SELECT chm_id, chm_name, chm_category FROM checklist_master WHERE chm_id = %d"
    result: DBResult = db.execute_query(query, (master_id,))
    if not result:
        return None
    chm_id, chm_name, chm_category = result[0]
    return ChecklistMaster(id=chm_id, name=chm_name, category=chm_category)


def get_all_checklist_masters(db: "DatabaseConnection") -> list[ChecklistMaster]:
    """Retrieves all checklist masters."""
    query = "SELECT chm_id, chm_name, chm_category FROM checklist_master order by chm_category, chm_name"
    results: DBResult = db.execute_query(query)
    if not results:
        return []
    return [ChecklistMaster(id=row[0], name=row[1], category=row[2]) for row in results]


def get_checklist_masters_by_category(db: "DatabaseConnection", category: str) -> list[ChecklistMaster]:
    """Retrieves all checklist masters by category."""
    query = "SELECT chm_id, chm_name, chm_category FROM checklist_master WHERE chm_category = %s order by chm_category, chm_name"
    results: DBResult = db.execute_query(query, (category,))
    if not results:
        return []
    return [ChecklistMaster(id=row[0], name=row[1], category=row[2]) for row in results]


def update_checklist_master(db: "DatabaseConnection", master: ChecklistMaster) -> None:
    """Updates a checklist master's name."""
    query = "UPDATE checklist_master SET chm_name = %s, chm_category = %s WHERE chm_id = %d"
    db.execute_query(query, (master.name, master.category, master.id))
    db.commit()


def delete_checklist_master(db: "DatabaseConnection", master_id: int) -> None:
    """Deletes a checklist master."""
    query = "DELETE FROM checklist_master WHERE chm_id = %d"
    db.execute_query(query, (master_id,))
    db.commit()
# endregion


# region ChecklistQuestion CRUD
def create_checklist_question(db: "DatabaseConnection", text: str, order: int, master_id: int) -> ChecklistQuestion:
    """Creates a new checklist question."""
    query = "INSERT INTO checklist_questions (chq_text, chq_order, chq_chmid) OUTPUT INSERTED.* VALUES (%s, %d, %d)"
    result: DBResult = db.execute_query(query, (text, order, master_id))
    if not result:
        raise RuntimeError("Failed to create checklist question.")
    db.commit()
    chq_id, chq_text, chq_order, chq_chmid = result[0]
    return ChecklistQuestion(id=chq_id, text=chq_text, order=chq_order, master_id=chq_chmid)


def get_checklist_question(db: "DatabaseConnection", question_text: int) -> Optional[ChecklistQuestion]:
    """Retrieves a single checklist question by its ID."""
    query = "SELECT chq_id, chq_text, chq_order, chq_chmid FROM checklist_questions WHERE chq_id = %d order by chq_order ASC"
    result: DBResult = db.execute_query(query, (question_text,))
    if not result:
        return None
    chq_id, chq_text, chq_order, chq_chmid = result[0]
    return ChecklistQuestion(id=chq_id, text=chq_text, order=chq_order, master_id=chq_chmid)


def get_questions_for_master(db: "DatabaseConnection", master_name: int) -> list[ChecklistQuestion]:
    """Retrieves all questions for a given checklist master, ordered by 'order'."""
    query = "SELECT chq_id, chq_text, chq_order, chq_chmid FROM checklist_questions WHERE chq_chmid = %d ORDER BY chq_order"
    results: DBResult = db.execute_query(query, (master_name,))
    if not results:
        return []
    return [ChecklistQuestion(id=row[0], text=row[1], order=row[2], master_id=row[3]) for row in results]


def update_checklist_question(db: "DatabaseConnection", question: ChecklistQuestion) -> None:
    """Updates a checklist question."""
    query = "UPDATE checklist_questions SET chq_text = %s, chq_order = %d, chq_chmid = %d WHERE chq_id = %d"
    db.execute_query(query, (question.text, question.order,
                     question.master_id, question.id))
    db.commit()


def delete_checklist_question(db: "DatabaseConnection", question_text: int) -> None:
    """Deletes a checklist question."""
    query = "DELETE FROM checklist_questions WHERE chq_id = %d"
    db.execute_query(query, (question_text,))
    db.commit()
# endregion


# region Checklist CRUD
def create_checklist(db: "DatabaseConnection", datum: datetime, completed: bool, master_name: str) -> Checklist:
    """Creates a new checklist instance."""
    query = "INSERT INTO checklists (chk_datum, chk_completed, chk_master_name) OUTPUT INSERTED.* VALUES (%s, %d, %d)"
    result: DBResult = db.execute_query(
        query, (datum, 1 if completed else 0, master_name))
    if not result:
        raise RuntimeError("Failed to create checklist.")
    chk_id, chk_datum, chk_completed, chk_master_name = result[0]
    return Checklist(id=chk_id, datum=chk_datum, completed=chk_completed, master_name=chk_master_name)


def get_checklist(db: "DatabaseConnection", checklist_id: int) -> Optional[Checklist]:
    """Retrieves a single checklist instance by its ID."""
    query = "SELECT chk_id, chk_datum, chk_completed, chk_master_name FROM checklists WHERE chk_id = %d"
    result: DBResult = db.execute_query(query, (checklist_id,))
    if not result:
        return None
    chk_id, chk_datum, chk_completed, chk_master_name = result[0]
    return Checklist(id=chk_id, datum=chk_datum, completed=chk_completed, master_name=chk_master_name)


def get_all_checklists(db: "DatabaseConnection") -> list[Checklist]:
    """Retrieves all checklist instances."""
    query: LiteralString = "select chk_id, chk_datum, chk_completed, chk_master_name from checklists"
    result: DBResult = db.execute_query(query)
    if not result:
        return []
    return [Checklist(id=row[0], datum=row[1], completed=row[2], master_name=row[3]) for row in result]


def get_checklists_for_master(db: "DatabaseConnection", master_name: int) -> list[Checklist]:
    """Retrieves all checklist instances for a given master, ordered by date descending."""
    query = "SELECT chk_id, chk_datum, chk_completed, chk_master_name FROM checklists WHERE chk_master_name = %d ORDER BY chk_datum DESC"
    results: DBResult = db.execute_query(query, (master_name,))
    if not results:
        return []
    return [Checklist(id=row[0], datum=row[1], completed=row[2], master_name=row[3]) for row in results]


def update_checklist(db: "DatabaseConnection", checklist: Checklist) -> None:
    """Updates a checklist instance."""
    query = "UPDATE checklists SET chk_datum = %s, chk_completed = %d, chk_master_name = %d WHERE chk_id = %d"
    db.execute_query(query, (checklist.datum,
                     1 if checklist.completed else 0, checklist.master_name, checklist.id))


def delete_checklist(db: "DatabaseConnection", checklist_id: int) -> None:
    """Deletes a checklist instance."""
    query = "DELETE FROM checklists WHERE chk_id = %d"
    db.execute_query(query, (checklist_id,))
# endregion


# region ChecklistAnswer CRUD
def create_checklist_answer(db: "DatabaseConnection", checklist_id: int, question_text: str, choice: Optional[bool]) -> ChecklistAnswer:
    """Creates a new checklist answer."""
    query = "INSERT INTO checklist_answers (cha_chkid, cha_question_text, cha_choice) OUTPUT INSERTED.* VALUES (%d, %d, %s)"
    result: DBResult = db.execute_query(
        query, (checklist_id, question_text, choice))
    if not result:
        raise RuntimeError("Failed to create checklist answer.")
    cha_id, cha_chkid, cha_question_text, cha_choice = result[0]
    return ChecklistAnswer(id=cha_id, checklist_id=cha_chkid, question_text=cha_question_text, choice=cha_choice)


def get_checklist_answer(db: "DatabaseConnection", answer_id: int) -> Optional[ChecklistAnswer]:
    """Retrieves a single checklist answer by its ID."""
    query = "SELECT cha_id, cha_chkid, cha_question_text, cha_choice FROM checklist_answers WHERE cha_id = %d"
    result: DBResult = db.execute_query(query, (answer_id,))
    if not result:
        return None
    cha_id, cha_chkid, cha_question_text, cha_choice = result[0]
    return ChecklistAnswer(id=cha_id, checklist_id=cha_chkid, question_text=cha_question_text, choice=cha_choice)


def get_answers_for_checklist(db: "DatabaseConnection", checklist_id: int) -> list[ChecklistAnswer]:
    """Retrieves all answers for a given checklist instance."""
    query = "SELECT cha_id, cha_chkid, cha_question_text, cha_choice FROM checklist_answers WHERE cha_chkid = %d order by cha_order"
    results: DBResult = db.execute_query(query, (checklist_id,))
    if not results:
        return []
    return [ChecklistAnswer(id=row[0], checklist_id=row[1], question_text=row[2], choice=row[3]) for row in results]


def update_checklist_answer(db: "DatabaseConnection", answer: ChecklistAnswer) -> None:
    """Updates a checklist answer."""
    query = "UPDATE checklist_answers SET cha_chkid = %d, cha_question_text = %d, cha_choice = %s WHERE cha_id = %d"
    db.execute_query(query, (answer.checklist_id,
                     answer.question_text, answer.choice, answer.id))
    db.commit()


def delete_checklist_answer(db: "DatabaseConnection", answer_id: int) -> None:
    """Deletes a checklist answer."""
    query = "DELETE FROM checklist_answers WHERE cha_id = %d"
    db.execute_query(query, (answer_id,))
# endregion
