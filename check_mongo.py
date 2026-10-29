from dotenv import load_dotenv

from db import ensure_connection


def main() -> None:
    load_dotenv()
    ensure_connection()
    print("MongoDB connection OK")


if __name__ == "__main__":
    main()
