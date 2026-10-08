users = {
    "blockchain_dev": {
        "role": "blockchain_developer",
        "clearance": 3,
        "department": "Blockchain",
        "active": True,
    },
    "smart_contract_auditor": {
        "role": "contract_auditor",
        "clearance": 3,
        "department": "Audit",
        "active": True,
    },
    "crypto_trader": {
        "role": "trader",
        "clearance": 2,
        "department": "Trading",
        "active": True,
    },
    "wallet_user": {
        "role": "wallet_user",
        "clearance": 1,
        "department": "Users",
        "active": True,
    },
    "mining_pool": {
        "role": "miner",
        "clearance": 1,
        "department": "Mining",
        "active": False,
    },
}
resources = [
    ("smart_contracts", 3),
    ("audit_reports", 3),
    ("trading_algorithms", 2),
    ("wallet_interface", 1),
    ("private_keys", 3),
    ("public_blockchain", 1),
    ("defi_protocols", 3),
    ("validator_nodes", 3),
    ("market_data", 2),
    ("community_forum", 1),
]
security_levels = (
    "Public Blockchain",
    "Permissioned",
    "Private Network",
    "Institutional",
)
blocked_users = {"mining_pool", "flash_loan_attack", "rug_pull_scam"}

resources_copy = resources.copy()


def renaming_res(resources, sec_levels):
    return [(name, security_levels[level - 1]) for name, level in resources]


def checking_access() -> None:
    for user in users:
        for res_name, res_lvl in resources:
            if user not in users:
                access = "DENY (User not found)"
            elif user in blocked_users:
                access = "DENY (User is blocked)"
            elif users.get(user).get("active") == False:
                access = "DENY (Account inactive)"
            elif users.get(user).get("clearance") >= res_lvl:
                access = "ALLOW"
            else:
                access = "DENY (Insufficient clearance)"
            print(f"user = '{user}'; resource = '{res_name}' -> {access}")


def main() -> None:
    renaming_res(resources, security_levels)

    checking_access()


if __name__ == "__main__":
    main()
