# CineVault OS — Local Dev User Directory (best-effort display-name resolution)
#
# This system has no persisted user-profile table: identity is a native JWT
# `sub` deterministically hashed to a UUID (see PLAN.md Part 2 grounding
# notes), so there is nowhere to look up an arbitrary user's real name given
# their UUID. The only UUID->identity mapping that exists anywhere in this
# codebase is the fixed local-dev credential store below (moved here from
# routers/auth.py so routers/social.py can reuse it without a router-to-router
# import). Real staging/production users (registered via /v1/auth/register,
# not one of the fixed local-dev accounts) will not match anything here —
# resolve_display_name() returns (None, None) for them, and callers must
# render an honest fallback rather than fabricate a name.

import os
from typing import Dict, Iterable, Optional, Tuple


def load_local_user_store() -> Dict[str, dict]:
    """
    Builds the local dev credential store from environment variables.
    Schema: { email: { "hash": bcrypt_hash, "user_id": uuid_str, "roles": [...] } }

    P0 Fix (Day 1-7 remediation): the previous store baked a hardcoded
    system_admin credential (`mann_068` / bcrypt hash committed in source)
    directly into this function, and the login page rendered it to any
    unauthenticated visitor. Privileged accounts must now be opted into
    explicitly via environment variables — no privileged hash ships in
    source, and nothing is rendered unless the operator configures it.
    """
    store = {
        os.getenv("DEV_USER_EMAIL", "dev@cinevault.local"): {
            "hash": os.getenv(
                "DEV_USER_PASSWORD_HASH",
                # Hash for password "devpass"
                "$2b$12$PVfblhI8qmxxO1ZbUoqIr.U.zkYngh4J9jLz5MxXcyCZPUB69DstG",
            ),
            "user_id": os.getenv(
                "DEV_USER_UUID",
                "018f0000-0000-7000-8000-000000000001",
            ),
            "roles": ["authenticated_user"],
        },
        os.getenv("DEV_CURATOR_EMAIL", "curator@cinevault.local"): {
            "hash": os.getenv(
                "DEV_CURATOR_PASSWORD_HASH",
                # Hash for password "curatorpass"
                "$2b$12$Yw5cy4oqZ80UoPxN/22V3uxLLYR73Dhy2dFGGBHJafogPcCUXVhXS",
            ),
            "user_id": os.getenv(
                "DEV_CURATOR_UUID",
                "018f0000-0000-7000-8000-000000000002",
            ),
            "roles": ["authenticated_user", "curator"],
        },
    }

    # Admin account is strictly opt-in via DEV_ADMIN_PASSWORD_HASH
    admin_hash = os.getenv("DEV_ADMIN_PASSWORD_HASH")
    if admin_hash:
        admin_email = os.getenv("DEV_ADMIN_EMAIL", "admin@cinevault.local")
        store[admin_email] = {
            "hash": admin_hash,
            "user_id": os.getenv(
                "DEV_ADMIN_UUID",
                "018f0000-0000-7000-8000-000000000003",
            ),
            "roles": ["authenticated_user", "curator", "system_admin"],
        }
        alt_admin_email = os.getenv("DEV_ADMIN_ALT_EMAIL")
        if alt_admin_email and alt_admin_email not in store:
            store[alt_admin_email] = store[admin_email]

    return store


def resolve_display_name(user_id: object) -> Tuple[Optional[str], Optional[str]]:
    """
    Best-effort reverse lookup: given a user UUID (or anything str()-able),
    returns (name, username) if it matches one of the fixed local-dev accounts
    above, else (None, None). There's no separate display-name field in the
    store, so both name and username are derived the same way login() does:
    the email's local part (e.g. "dev@cinevault.local" -> "dev").

    For resolving many ids at once (e.g. enriching a list of recommendations
    or friendships), prefer resolve_display_names() -- this single-id version
    reloads the store on every call.
    """
    names = resolve_display_names([user_id])
    return names.get(str(user_id), (None, None))


def resolve_display_names(user_ids: Iterable[object]) -> Dict[str, Tuple[Optional[str], Optional[str]]]:
    """
    Batch form of resolve_display_name(): loads the store once and resolves
    every id in `user_ids`, returning {str(user_id): (name, username)}. Ids
    that don't match a fixed local-dev account map to (None, None).
    """
    targets = {str(uid) for uid in user_ids}
    by_user_id = {
        str(record.get("user_id")): email.split("@")[0]
        for email, record in load_local_user_store().items()
    }
    return {
        target: ((by_user_id[target], by_user_id[target]) if target in by_user_id else (None, None))
        for target in targets
    }
