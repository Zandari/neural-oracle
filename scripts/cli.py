import argparse
import os
import uuid
import asyncio
from app.repository import SQLiteRepository
from app.models import User
from app.security import hash_access_token


async def list_users(uri: str):
    async with SQLiteRepository.from_uri(uri) as repo:
        await repo.init_database()
        users = await repo.get_users()
        for user in users:
            print(f"ID: {user.id}, Name: {user.name}, Hashed Token: {user.hashed_access_token[:20]}...")


async def add_user(uri: str, name: str):
    access_token = str(uuid.uuid4())

    hashed_token = hash_access_token(access_token)

    user = User(id=None, name=name, hashed_access_token=hashed_token)
    async with SQLiteRepository.from_uri(uri) as repo:
        await repo.init_database()
        success = await repo.put_user(user)
        if success:
            print("="*40)
            print(f"User added successfully!")
            print(f"Name: {name}")
            print(f"Access Token (save this - it won't be shown again):")
            print(f"{access_token}")
            print("="*40)
        else:
            print("Failed to add user.")


async def remove_user(uri: str, user_id: int):
    async with SQLiteRepository.from_uri(uri) as repo:
        await repo.init_database()
        success = await repo.delete_user_by_id(user_id)
        if success:
            print(f"Removed user with ID: {user_id}")
        else:
            print(f"User with ID {user_id} not found")


def main():
    parser = argparse.ArgumentParser(description='User manager CLI utility')
    parser.add_argument('--uri', default=os.getenv("SQLITE_URI", "database.db"), help='SQLite URI')

    subparsers = parser.add_subparsers(dest='command', required=True)

    subparsers.add_parser('list', help='List all users')

    add_parser = subparsers.add_parser('add', help='Add a new user')
    add_parser.add_argument('name', help='User name')

    remove_parser = subparsers.add_parser('remove', help='Remove user by ID')
    remove_parser.add_argument('id', type=int, help='User ID')

    args = parser.parse_args()
    uri = args.uri

    if args.command == 'list':
        asyncio.run(list_users(uri))
    elif args.command == 'add':
        asyncio.run(add_user(uri, args.name))
    elif args.command == 'remove':
        asyncio.run(remove_user(uri, args.id))


if __name__ == "__main__":
    main()
