import math
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, Integer, Boolean, ForeignKey, DateTime, select, desc
from redis.asyncio import Redis
from config import DATABASE_URL, REDIS_URL, LEVEL_TITLES, IST

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(100))
    full_name: Mapped[str] = mapped_column(String(150), default="Arena Warrior")
    xp: Mapped[int] = mapped_column(Integer, default=0)
    coins: Mapped[int] = mapped_column(Integer, default=100)
    tickets: Mapped[int] = mapped_column(Integer, default=3)
    level: Mapped[int] = mapped_column(Integer, default=1)

    games_played: Mapped[int] = mapped_column(Integer, default=0)
    quiz_wins: Mapped[int] = mapped_column(Integer, default=0)
    quiz_correct: Mapped[int] = mapped_column(Integer, default=0)
    imposter_wins: Mapped[int] = mapped_column(Integer, default=0)
    imposter_catches: Mapped[int] = mapped_column(Integer, default=0)
    mafia_wins: Mapped[int] = mapped_column(Integer, default=0)
    town_wins: Mapped[int] = mapped_column(Integer, default=0)
    eliminations: Mapped[int] = mapped_column(Integer, default=0)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)

    equipped_border: Mapped[str] = mapped_column(String(60), default="Standard")
    equipped_title: Mapped[str | None] = mapped_column(String(60), default=None)
    last_daily: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class UserItem(Base):
    __tablename__ = "user_items"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    item_id: Mapped[str] = mapped_column(String(50))
    item_type: Mapped[str] = mapped_column(String(20))


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), primary_key=True)
    ach_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(IST))


class GroupMemberStats(Base):
    __tablename__ = "group_member_stats"
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), primary_key=True)
    group_xp: Mapped[int] = mapped_column(Integer, default=0)
    group_wins: Mapped[int] = mapped_column(Integer, default=0)


def calculate_level(xp: int) -> int:
    return math.floor(xp / 500) + 1


def get_rank_title(level: int, custom_title: str | None = None) -> str:
    if custom_title:
        return custom_title
    for max_lvl, title in LEVEL_TITLES:
        if level <= max_lvl:
            return title
    return "🌌 Arena God"


async def ensure_user(user_id: int, username: str | None, full_name: str) -> User:
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            user = User(telegram_id=user_id, username=username, full_name=full_name)
            session.add(user)
            await session.commit()
        else:
            user.username = username
            user.full_name = full_name
            await session.commit()
        return user


async def record_progression(
    user_id: int,
    chat_id: int | None,
    xp: int = 0,
    coins: int = 0,
    won_mode: str | None = None,
    played: bool = True,
):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            return
        user.xp += xp
        user.coins += coins
        user.level = calculate_level(user.xp)
        if played:
            user.games_played += 1

        if won_mode:
            user.current_streak += 1
            user.best_streak = max(user.best_streak, user.current_streak)
            if won_mode == "quiz":
                user.quiz_wins += 1
            elif won_mode == "imposter":
                user.imposter_wins += 1
            elif won_mode == "mafia":
                user.mafia_wins += 1
            elif won_mode == "town":
                user.town_wins += 1
        elif played:
            user.current_streak = 0

        if chat_id and chat_id < 0:
            g_stat = await session.get(GroupMemberStats, (chat_id, user_id))
            if not g_stat:
                g_stat = GroupMemberStats(chat_id=chat_id, user_id=user_id)
                session.add(g_stat)
            g_stat.group_xp += xp
            if won_mode:
                g_stat.group_wins += 1

        await session.commit()

    # Daily & Weekly Redis mission tracking
    today = datetime.now(IST).strftime("%Y-%m-%d")
    week = datetime.now(IST).strftime("%Y-W%W")
    if xp > 0:
        await redis_client.hincrby(f"mission:w:{user_id}:{week}", "xp", xp)
    if won_mode:
        await redis_client.hincrby(f"mission:d:{user_id}:{today}", f"win_{won_mode}", 1)
        await redis_client.hincrby(f"mission:w:{user_id}:{week}", "wins", 1)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
          
