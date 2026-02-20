
# Brazilian Civic Manifestation & Voting Web Application

This repository contains a **prototype implementation** of the high‑level design described in our architecture notes for a civic participation platform for Brazil.  The goal of the system is to allow citizens to register their presence at public demonstrations and cast votes on political themes using their **gov.br** identities in a way that balances integrity, privacy, and transparency.

> **Disclaimer:** This prototype is intended for demonstration and educational purposes only.  It illustrates the core flows and data structures described in the design document but does **not** implement every security, antifraud, or cryptographic measure required for a production deployment.  In particular, the integration with Gov.br for identity verification, device attestation, proof‑of‑presence, blind signature issuance, and blockchain anchoring are simplified or stubbed out here.  You should treat this repository as a starting point for further development, not a final product.

## Project structure

```text
br_manifest_app/
├── backend/
│   ├── __init__.py
│   ├── anchor.py        # stub for blockchain anchoring
│   ├── auth.py          # simple token‑based authentication stub
│   ├── database.py      # in‑memory storage for events, check‑ins, themes, votes
│   ├── hashing.py       # helpers for salted hashing of CPF and tokens
│   ├── main.py          # FastAPI application exposing REST endpoints
│   ├── merkle.py        # minimal Merkle tree implementation
│   └── models.py        # Pydantic request/response models
├── frontend/
│   ├── index.html       # simple user interface for demonstration
│   ├── script.js        # client‑side logic to interact with the API
│   └── styles.css       # basic styling
└── README.md            # this file
```

## Running the API server

The backend is built with **FastAPI** and requires Python 3.10+.  To run the server locally, create a virtual environment and install the dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic
cd backend
uvicorn main:app --reload
```

The API will be accessible at `http://localhost:8000`.  When run in development mode, the interactive documentation is available at `/docs`.

## Key features implemented

* **Login** – Users supply a CPF (and optionally a name) to obtain a bearer token.  The real system would delegate to Gov.br using OIDC; here we simply generate a random token and store the mapping in memory.
* **Event management** – Administrators can create events with a name, description, geofence (latitude, longitude, radius) and a start/stop window.  Anyone can list events.
* **Check‑in** – An authenticated user can register their presence at an event by sending their coordinates (and optionally a photo encoded as base64).  The server verifies that the request time is within the allowed window and that the location falls inside the declared radius.  It hashes the user’s CPF with a per‑event salt, stores a record, and adds the leaf to a Merkle tree.  The Merkle root for the batch of check‑ins can be obtained via `/merkleRoots`.
* **Vote themes** – Admins can create themes/questions with multiple options.  Users can request a single‑use token for a theme and then cast a vote using that token.  The token issuance process stands in for the blind signature scheme described in the design; here it simply creates a random string and associates it with a user and theme.  Vote aggregation is available at `/votes/{theme_id}/aggregate`.
* **Merkle tree** – The `merkle.py` module contains a minimal Merkle tree implementation based on SHA‑256.  After each check‑in or vote, the server rebuilds the root for the relevant batch.  A stubbed `anchor.py` appends each new root to a local log with a timestamp to simulate anchoring on a blockchain.

## Extending this prototype

* **Gov.br authentication** – Replace `auth.py` with a proper OpenID Connect integration.  FastAPI supports asynchronous authentication schemes; you could implement the OIDC authorization code flow with PKCE using the [`python‑oidc`](https://pypi.org/project/python‑oidc/) or [`authlib`](https://docs.authlib.org/en/latest/) packages.
* **Data persistence** – The current implementation stores everything in process memory.  For a real deployment, substitute `database.py` with a persistent solution such as PostgreSQL (via SQLAlchemy), Redis for session storage, and object storage (e.g., S3) for photo uploads and Merkle proof bundles.
* **Blind signatures and cryptography** – The voting subsystem presently associates tokens with users.  To achieve unlinkability, implement a blind signature protocol or another credential system (e.g. Coconut, BLS blind signatures) and store only commitments.  See our design notes for details.
* **Anti‑fraud measures** – This example performs a simple geofence check but does not attempt to detect GPS spoofing, root/jailbreak, emulator usage, or multiple registrations from the same device.  A production system would integrate device attestation APIs (Google Play Integrity, Apple DeviceCheck), beacon verification, and cross‑device anomaly detection.
* **Blockchain anchoring** – The `anchor.py` module currently writes Merkle roots to a text file.  You can replace this with a client to a permissioned Hyperledger Besu network and an Ethereum L2 for public anchoring as described in the architecture document.

## Front‑end prototype

The `frontend` folder contains a very basic HTML page with JavaScript to demonstrate the flows.  It allows a user to:

1. Log in by entering a CPF and name.
2. View the list of events and create a new one (when acting as an admin).
3. Check in to an event (with simulated geolocation using the browser’s geolocation API).
4. View existing vote themes and create new ones.
5. Request a voting token and cast a vote.

This front‑end is intentionally simplistic; a real PWA would need offline queuing, better UI/UX, security hardening and device attestation support.
