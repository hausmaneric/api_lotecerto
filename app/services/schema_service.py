from sqlalchemy import text
from sqlalchemy.engine import Engine


class SchemaService:
    @staticmethod
    def ensure_schema(engine: Engine) -> None:
        if not str(engine.url).startswith("sqlite"):
            return

        with engine.begin() as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    text("SELECT name FROM sqlite_master WHERE type = 'table'")
                )
            }

            if "farms" in tables:
                SchemaService._add_column_if_missing(
                    connection,
                    "farms",
                    "owner_name",
                    "ALTER TABLE farms ADD COLUMN owner_name TEXT",
                )

            if "api_users" in tables:
                SchemaService._add_column_if_missing(
                    connection,
                    "api_users",
                    "farm_id",
                    "ALTER TABLE api_users ADD COLUMN farm_id TEXT",
                )
                SchemaService._add_column_if_missing(
                    connection,
                    "api_users",
                    "role",
                    "ALTER TABLE api_users ADD COLUMN role TEXT NOT NULL DEFAULT 'member'",
                )

            if "vaccines" in tables:
                SchemaService._add_column_if_missing(
                    connection,
                    "vaccines",
                    "farm_id",
                    "ALTER TABLE vaccines ADD COLUMN farm_id TEXT",
                )

            if "app_settings" in tables:
                SchemaService._add_column_if_missing(
                    connection,
                    "app_settings",
                    "farm_id",
                    "ALTER TABLE app_settings ADD COLUMN farm_id TEXT",
                )
                SchemaService._add_column_if_missing(
                    connection,
                    "app_settings",
                    "has_completed_onboarding",
                    "ALTER TABLE app_settings ADD COLUMN has_completed_onboarding INTEGER NOT NULL DEFAULT 0",
                )

            if "deleted_entities" in tables:
                SchemaService._add_column_if_missing(
                    connection,
                    "deleted_entities",
                    "farm_id",
                    "ALTER TABLE deleted_entities ADD COLUMN farm_id TEXT",
                )

            if "farms" in tables:
                connection.execute(
                    text(
                        """
                        INSERT INTO farms (id, name, owner_name, created_at, updated_at)
                        SELECT 'default-farm', 'Minha Fazenda', 'Administrador', CURRENT_TIMESTAMP, NULL
                        WHERE NOT EXISTS (SELECT 1 FROM farms WHERE id = 'default-farm')
                        """
                    )
                )

            if "api_users" in tables:
                connection.execute(
                    text(
                        """
                        UPDATE api_users
                        SET farm_id = COALESCE(farm_id, 'default-farm'),
                            role = COALESCE(role, 'owner')
                        WHERE farm_id IS NULL OR role IS NULL
                        """
                    )
                )

            if "vaccines" in tables:
                connection.execute(
                    text(
                        """
                        UPDATE vaccines
                        SET farm_id = COALESCE(farm_id, 'default-farm')
                        WHERE farm_id IS NULL
                        """
                    )
                )

            if "app_settings" in tables:
                connection.execute(
                    text(
                        """
                        UPDATE app_settings
                        SET farm_id = COALESCE(farm_id, 'default-farm'),
                            has_completed_onboarding = COALESCE(has_completed_onboarding, 0)
                        WHERE farm_id IS NULL OR has_completed_onboarding IS NULL
                        """
                    )
                )

            if "deleted_entities" in tables:
                connection.execute(
                    text(
                        """
                        UPDATE deleted_entities
                        SET farm_id = COALESCE(farm_id, 'default-farm')
                        WHERE farm_id IS NULL
                        """
                    )
                )

    @staticmethod
    def _add_column_if_missing(connection, table_name: str, column_name: str, ddl: str) -> None:
        columns = {
            row[1]
            for row in connection.execute(text(f"PRAGMA table_info({table_name})"))
        }
        if column_name not in columns:
            connection.execute(text(ddl))
