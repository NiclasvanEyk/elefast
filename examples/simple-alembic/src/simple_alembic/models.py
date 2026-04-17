from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column


class Base(MappedAsDataclass, DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    slug: Mapped[str] = mapped_column(primary_key=True)
    headline: Mapped[str]
    body: Mapped[str]
