from sqlalchemy import BigInteger, create_engine, Integer
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, sessionmaker
import atexit
import datetime


con_string = 'sqlite:///db/database.db'

engine = create_engine(con_string)
Session = sessionmaker(bind=engine, expire_on_commit=False)

atexit.register(engine.dispose)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'user'
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(nullable=True)
    first_name: Mapped[str] = mapped_column(nullable=True)
    last_name: Mapped[str] = mapped_column(nullable=True)
    time_start: Mapped[datetime.datetime] = mapped_column(nullable=True)


class Order(Base):
    __tablename__ = 'order'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    username: Mapped[str] = mapped_column(nullable=True)
    first_name: Mapped[str] = mapped_column(nullable=True)
    last_name: Mapped[str] = mapped_column(nullable=True)
    phone: Mapped[str] = mapped_column(nullable=True)
    fio: Mapped[str] = mapped_column(nullable=True)
    time_order: Mapped[datetime.datetime] = mapped_column(nullable=True)


def create_tables():
    Base.metadata.create_all(engine)