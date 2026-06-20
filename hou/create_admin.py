import argparse
import asyncio

from models import AsyncSessionFactory
from models.user import User
from repository.user_repo import UserRepository
from schemas.user_schemas import UserCreateSchema


async def create_admin(email: str, username: str, password: str) -> None:
    async with AsyncSessionFactory() as session:
        user_repository = UserRepository(session=session)
        user = await user_repository.get_user_by_email(email)

        if user:
            user.username = username
            user.is_admin = True
            if password:
                user.password = password
            await session.commit()
            print(f"管理员已更新: {email}")
            return

        admin = UserCreateSchema(
            email=email,
            username=username,
            password=password,
            is_admin=True,
        )
        await user_repository.create_user(admin)
        print(f"管理员已创建: {email}")


def parse_args():
    parser = argparse.ArgumentParser(description="Create or update an admin user.")
    parser.add_argument("--email", required=True, help="Admin email.")
    parser.add_argument("--username", required=True, help="Admin username.")
    parser.add_argument("--password", required=True, help="Admin password.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(create_admin(args.email, args.username, args.password))
