from sqlalchemy import create_engine, select, desc
from sqlalchemy.orm import Session
from user_entity import UserEntity

engine = create_engine("sqlite:///happy.db")

with Session(engine) as session:
    query = select(UserEntity).order_by(desc(UserEntity.id))
    for user in session.scalars(query):
        print(user.id, user.username, user.password)

    newName = input("新的用户名：")
    newPassword = input("新的密码：")
    newUser = UserEntity(username=newName, password=newPassword)
    session.add(newUser)
    session.flush()

    query = select(UserEntity).order_by(desc(UserEntity.id))
    for user in session.scalars(query):
        print(user.id, user.username, user.password)

    user_id_to_delete = int(input("要删除的用户ID："))
    user_to_delete = session.get(UserEntity, user_id_to_delete)
    if user_to_delete is not None:
        session.delete(user_to_delete)
        print(f"用户 {user_id_to_delete} 已删除。")
        session.flush()

    query = select(UserEntity).order_by(desc(UserEntity.id))
    for user in session.scalars(query):
        print(user.id, user.username, user.password)
    session.commit()
