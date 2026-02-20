from __future__ import annotations

CONSTRAINTS = [
    "CREATE CONSTRAINT unique_person IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT unique_bill IF NOT EXISTS FOR (n:Bill) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT unique_vote_event IF NOT EXISTS FOR (n:VoteEvent) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT unique_vote_action IF NOT EXISTS FOR (n:VoteAction) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT unique_expense IF NOT EXISTS FOR (n:Expense) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT unique_organization IF NOT EXISTS FOR (n:Organization) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT unique_party IF NOT EXISTS FOR (n:Party) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT unique_state IF NOT EXISTS FOR (n:State) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT unique_committee IF NOT EXISTS FOR (n:Committee) REQUIRE n.id IS UNIQUE",
]
