# crud/statistics.py

from sqlalchemy.orm import Session
from sqlalchemy import func
from models.statistics import Statistic, StatisticValue
from schemas.statistics import StatisticCreate, StatisticUpdate, StatisticValueCreate
from uuid import UUID
import uuid

def create_statistic(db: Session, statistic: StatisticCreate, user_id: UUID):
    db_statistic = Statistic(
        id=uuid.uuid4(),
        name=statistic.name,
        description=statistic.description,
        icon=statistic.icon,
        type=statistic.type,
        user_id=user_id
    )
    db.add(db_statistic)
    db.commit()
    db.refresh(db_statistic)
    return db_statistic

def get_statistic(db: Session, statistic_id: UUID):
    return db.query(Statistic).filter(Statistic.id == statistic_id).first()

def get_user_statistics(db: Session, user_id: UUID):
    return db.query(Statistic).filter(Statistic.user_id == user_id).all()

def update_statistic(db: Session, statistic_id: UUID, statistic_update: StatisticUpdate):
    db_statistic = get_statistic(db, statistic_id)
    if not db_statistic:
        return None
    for key, value in statistic_update.dict(exclude_unset=True).items():
        setattr(db_statistic, key, value)
    db.commit()
    db.refresh(db_statistic)
    return db_statistic

def delete_statistic(db: Session, statistic_id: UUID):
    db_statistic = get_statistic(db, statistic_id)
    if db_statistic:
        db.delete(db_statistic)
        db.commit()
        return True
    return False
    
def create_statistic_value(db: Session, statistic_id: UUID, value: StatisticValueCreate):
    db_value = StatisticValue(
        id=uuid.uuid4(),
        statistic_id=statistic_id,
        time=value.time,
        number=value.number,
        boolean=value.boolean,
        text=value.text
    )
    db.add(db_value)
    db.commit()
    db.refresh(db_value)
    return db_value

def delete_statistic_value(db: Session, statistic_id: UUID):
    db_value = db.query(StatisticValue).filter(StatisticValue.statistic_id == statistic_id).first()
    if db_value:
        db.delete(db_value)
        db.commit()
        return True
    return False    

def get_statistic_type(db: Session, statistic_id: UUID):
    statistic = db.query(Statistic).filter(Statistic.id == statistic_id).first()
    return statistic.type if statistic else None

def delete_statistic_value(db: Session, statistic_id: UUID):
    db_value = db.query(StatisticValue).filter(StatisticValue.statistic_id == statistic_id).first()
    if db_value:
        db.delete(db_value)
        db.commit()
        return True
    return False

def reset_statistic(db: Session, statistic_id: UUID):
    db.query(StatisticValue).filter(StatisticValue.statistic_id == statistic_id).delete()
    db.commit()

def get_aggregated_statistic_value(db: Session, statistic_id: UUID):
    statistic = db.query(Statistic).filter(Statistic.id == statistic_id).first()
    if not statistic:
        return None

    statistic_type = statistic.type

    if statistic_type == "number":
        result = db.query(func.sum(StatisticValue.number)).filter(StatisticValue.statistic_id == statistic_id).scalar()
        return {"value": result}

    elif statistic_type == "time":
        result = db.query(func.avg(func.extract("epoch", StatisticValue.time))).filter(StatisticValue.statistic_id == statistic_id).scalar()
        average_time = None
        if result is not None:
            average_time = timedelta(seconds=result)
        return {"value": str(average_time)}

    elif statistic_type == "boolean":
        true_count = db.query(func.count()).filter(StatisticValue.statistic_id == statistic_id, StatisticValue.boolean == True).scalar()
        false_count = db.query(func.count()).filter(StatisticValue.statistic_id == statistic_id, StatisticValue.boolean == False).scalar()
        return {"value": { "true": true_count, "false": false_count } }

    return None

def reset_user_statistics(db: Session, user_id: UUID):
    user_statistics = db.query(Statistic).filter(Statistic.user_id == user_id).all()
    
    for statistic in user_statistics:
        db.query(StatisticValue).filter(StatisticValue.statistic_id == statistic.id).delete()
    
    db.commit()