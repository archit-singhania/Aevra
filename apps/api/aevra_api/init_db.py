"""Initialize a disposable/local database for the free staging profile."""

from aevra_api.db.base import Base
from aevra_api.db.session import engine


def main() -> None:
    Base.metadata.create_all(engine)
    print("VAE database ready")


if __name__ == "__main__":
    main()
