#!/usr/bin/env python3
"""Add one or more Formspree applications to the roster and render their emails.

Reads JSON on stdin - a single submission object, or a list of them - using the
form's own field names (email, name, room_preference, session_reports,
certification, journey_status, main_drive, expectations,
facilitation_challenges, anything_else, location_timezone, call_availability).

    echo '{"email":"a@b.com","name":"Asha", ...}' | python3 emails/new_applicant.py

Applicants are stored in emails/applicants.csv (gitignored, real personal
answers). Anyone already in that file by email is reported as a duplicate and
skipped, so re-running after a false start doesn't double up. Every applicant's
email is then re-rendered into emails/out/.

Prints, per new applicant, exactly what a Gmail draft needs:
  TO / SUBJECT / the .body.html path (htmlBody) / the .txt path (plain body).
"""

import csv
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROSTER = os.path.join(HERE, "applicants.csv")
OUT = os.path.join(HERE, "out")

COLUMNS = ["_date", "name", "email", "room_preference", "session_reports",
           "certification", "journey_status", "main_drive", "expectations",
           "facilitation_challenges", "anything_else", "location_timezone",
           "call_availability"]


def load_roster():
    if not os.path.exists(ROSTER):
        return []
    with open(ROSTER, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save_roster(rows):
    with open(ROSTER, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({c: (r.get(c) or "") for c in COLUMNS})


def main():
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit("no JSON on stdin - pipe in the submission(s)")
    try:
        incoming = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit("stdin is not valid JSON: %s" % e)
    if isinstance(incoming, dict):
        incoming = [incoming]

    roster = load_roster()
    known = {(r.get("email") or "").strip().lower() for r in roster}

    added = []
    for sub in incoming:
        email = (sub.get("email") or "").strip()
        if not email:
            print("  skipped: a submission has no email")
            continue
        if email.lower() in known:
            print("  duplicate, already on the roster: %s" % email)
            continue
        roster.append(sub)
        known.add(email.lower())
        added.append(sub)

    if not added:
        print("nothing new to add.")
        return

    save_roster(roster)
    subprocess.run([sys.executable, os.path.join(HERE, "build.py"), ROSTER],
                   check=True, stdout=subprocess.DEVNULL)

    print("\nadded %d applicant(s). Drafts to create:\n" % len(added))
    files = sorted(os.listdir(OUT))
    for sub in added:
        email = sub["email"].strip()
        name = (sub.get("name") or "").strip()
        first = name.split()[0] if name else ""
        stem = next((f[:-len(".body.html")] for f in files
                     if f.endswith(".body.html")
                     and email.lower().replace("@", "-").replace(".", "-") in f), None)
        print("  TO       %s" % email)
        print("  SUBJECT  We have your Level 2 application%s" % (", " + first if first else ""))
        print("  htmlBody %s" % os.path.join(OUT, stem + ".body.html") if stem else "  (render not found)")
        print("  textBody %s" % os.path.join(OUT, stem + ".txt") if stem else "")
        print()
    print("preview all: %s" % os.path.join(OUT, "index.html"))


if __name__ == "__main__":
    main()
