# CineVault OS — Production Secret Validation Regression Tests (Day 1-7 remediation)
# Proves the P0 fixes actually hold:
#   1. A staging/production ENVIRONMENT with any insecure dev-default secret
#      still active refuses to boot (raises), rather than running exposed.
#   2. local_development keeps working unmodified (no regression).
#   3. The hardcoded system_admin credential (Mann_068) no longer exists in
#      the local dev credential store, and admin access is opt-in only via
#      DEV_ADMIN_PASSWORD_HASH.

import importlib
import os
import unittest


class TestProductionSecretValidation(unittest.TestCase):
    def _reload_config(self):
        import services.api.config as config_module
        importlib.reload(config_module)
        return config_module

    def test_local_development_boots_with_defaults(self):
        env_backup = os.environ.get("ENVIRONMENT")
        os.environ.pop("ENVIRONMENT", None)
        try:
            config_module = self._reload_config()
            self.assertEqual(config_module.config.environment, "local_development")
        finally:
            if env_backup is not None:
                os.environ["ENVIRONMENT"] = env_backup
            self._reload_config()

    def test_production_refuses_to_boot_with_insecure_defaults(self):
        env_backup = os.environ.get("ENVIRONMENT")
        os.environ["ENVIRONMENT"] = "production"
        try:
            with self.assertRaises(Exception):
                self._reload_config()
        finally:
            if env_backup is not None:
                os.environ["ENVIRONMENT"] = env_backup
            else:
                os.environ.pop("ENVIRONMENT", None)
            self._reload_config()

    def test_production_boots_when_real_secrets_are_set(self):
        env_backup = {
            k: os.environ.get(k)
            for k in (
                "ENVIRONMENT",
                "JWT_SECRET_KEY",
                "POSTGRES_PASSWORD",
                "RABBITMQ_PASSWORD",
                "S3_ACCESS_KEY_ID",
                "S3_SECRET_ACCESS_KEY",
            )
        }
        os.environ.update(
            {
                "ENVIRONMENT": "production",
                "JWT_SECRET_KEY": "a-real-random-production-secret",
                "POSTGRES_PASSWORD": "a-real-random-pg-password",
                "RABBITMQ_PASSWORD": "a-real-random-rmq-password",
                "S3_ACCESS_KEY_ID": "AKIAREALKEYID",
                "S3_SECRET_ACCESS_KEY": "a-real-random-s3-secret",
            }
        )
        try:
            config_module = self._reload_config()
            self.assertEqual(config_module.config.environment, "production")
        finally:
            for k, v in env_backup.items():
                if v is not None:
                    os.environ[k] = v
                else:
                    os.environ.pop(k, None)
            self._reload_config()


class TestNoHardcodedAdminCredential(unittest.TestCase):
    def test_mann_068_not_in_local_user_store(self):
        from services.api.routers.auth import _load_local_user_store

        os.environ.pop("DEV_ADMIN_PASSWORD_HASH", None)
        store = _load_local_user_store()

        for email, record in store.items():
            self.assertNotIn(
                "mann_068", email.lower(),
                "Hardcoded Mann_068 credential must not exist in the dev user store.",
            )
            self.assertNotEqual(
                record.get("username", "").lower(), "mann_068",
                "Hardcoded Mann_068 username must not exist in the dev user store.",
            )

    def test_system_admin_absent_without_explicit_opt_in(self):
        from services.api.routers.auth import _load_local_user_store

        os.environ.pop("DEV_ADMIN_PASSWORD_HASH", None)
        store = _load_local_user_store()
        admin_records = [r for r in store.values() if "system_admin" in r.get("roles", [])]
        self.assertEqual(
            len(admin_records), 0,
            "No system_admin account should exist unless DEV_ADMIN_PASSWORD_HASH is explicitly set.",
        )

    def test_system_admin_present_when_explicitly_configured(self):
        from services.api.routers.auth import _load_local_user_store

        os.environ["DEV_ADMIN_PASSWORD_HASH"] = "$2b$12$fakehashfortestingonly0000000000000000000000000000"
        try:
            store = _load_local_user_store()
            admin_records = [r for r in store.values() if "system_admin" in r.get("roles", [])]
            self.assertEqual(len(admin_records), 1)
        finally:
            os.environ.pop("DEV_ADMIN_PASSWORD_HASH", None)


if __name__ == "__main__":
    unittest.main()
