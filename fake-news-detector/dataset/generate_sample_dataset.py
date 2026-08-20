"""
generate_sample_dataset.py

Generates a synthetic, offline-friendly Fake.csv / True.csv pair so the
whole project (train_model.py -> app.py) can run end-to-end with zero
external downloads.

IMPORTANT (read this):
This synthetic data is only meant to bootstrap the project so you can see
the full pipeline work immediately. For real, production-grade accuracy
you should replace dataset/Fake.csv and dataset/True.csv with the full
ISOT "Fake and Real News Dataset" (~12,600 rows each: True.csv from
Reuters.com, Fake.csv from flagged unreliable sources), commonly
distributed on Kaggle as "fake-and-real-news-dataset". Both files must
keep the same column names used here: title, text, subject, date.
Once you drop in the real files, just re-run:  python train_model.py
"""

import csv
import random
from pathlib import Path

random.seed(42)

DATASET_DIR = Path(__file__).resolve().parent

REAL_SUBJECTS = ["politicsNews", "worldnews", "business", "technology", "health"]
FAKE_SUBJECTS = ["News", "politics", "conspiracy", "left-news", "Government News"]

REAL_SOURCES = ["Reuters", "AP", "the finance ministry", "a government spokesperson", "officials"]
REAL_TOPICS = [
    "trade negotiations", "the annual budget", "a new infrastructure bill",
    "the central bank's interest rate decision", "election results",
    "a public health initiative", "climate policy talks", "a court ruling",
    "quarterly earnings", "a diplomatic summit", "unemployment figures",
    "a new education reform bill", "regional trade agreements",
    "a scientific research grant", "municipal budget allocations",
]
REAL_VERBS = ["announced", "confirmed", "reported", "said", "stated", "released data on"]
REAL_TEMPLATES = [
    "{source} {verb} details on {topic} on Wednesday, citing officials familiar with the matter.",
    "According to {source}, {topic} will be reviewed by lawmakers next month after committee hearings.",
    "{source} {verb} that {topic} remains on schedule, according to a statement released Tuesday.",
    "Data released by {source} shows steady progress on {topic}, according to people briefed on the matter.",
    "In a statement, {source} {verb} an update regarding {topic}, following weeks of negotiation.",
    "Officials confirmed to {source} that {topic} was discussed during a closed-door session on Monday.",
    "A spokesperson for {source} {verb} the latest figures on {topic} during a press briefing.",
]

FAKE_HOOKS = [
    "SHOCKING", "You Won't Believe", "BREAKING", "EXPOSED", "LEAKED",
    "URGENT", "Mainstream Media Won't Tell You", "EXCLUSIVE",
]
FAKE_CLAIMS = [
    "secret government plot", "miracle cure being hidden from the public",
    "celebrity scandal cover-up", "shocking conspiracy", "hidden agenda",
    "massive cover-up", "secret deal exposed", "banned study reveals the truth",
    "elite plan nobody is talking about", "hidden truth about the vaccine",
    "secret recording leaked online", "insider reveals shocking secret",
]
FAKE_TEMPLATES = [
    "{hook}: Insiders reveal the {claim} that will change everything you thought you knew!!!",
    "{hook} -- Doctors HATE this {claim}, share before it gets deleted!",
    "You won't believe what was just found about the {claim}; wake up before it's too late!",
    "{hook}: Anonymous source claims {claim}, and the mainstream media refuses to cover it.",
    "This {claim} is being suppressed by the elites -- click to see the forbidden photos!",
    "{hook}!!! The {claim} exposed by a whistleblower, share this NOW before they take it down!",
    "Experts are stunned after the {claim} was leaked; the truth they don't want you to see.",
]


def _make_real_row(i):
    source = random.choice(REAL_SOURCES)
    topic = random.choice(REAL_TOPICS)
    verb = random.choice(REAL_VERBS)
    template = random.choice(REAL_TEMPLATES)
    title = f"{source.title()} {verb} update on {topic}".replace("The ", "the ")
    body_sentences = [template.format(source=source, topic=topic, verb=verb) for _ in range(6)]
    text = " ".join(body_sentences)
    subject = random.choice(REAL_SUBJECTS)
    date = f"{random.randint(1,28)}-{random.choice(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])}-2025"
    return [title, text, subject, date]


def _make_fake_row(i):
    hook = random.choice(FAKE_HOOKS)
    claim = random.choice(FAKE_CLAIMS)
    template = random.choice(FAKE_TEMPLATES)
    title = f"{hook}: The {claim} nobody wants you to see"
    body_sentences = [template.format(hook=hook, claim=random.choice(FAKE_CLAIMS)) for _ in range(6)]
    text = " ".join(body_sentences)
    subject = random.choice(FAKE_SUBJECTS)
    date = f"{random.randint(1,28)}-{random.choice(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])}-2025"
    return [title, text, subject, date]


def generate(n_per_class: int = 600):
    header = ["title", "text", "subject", "date"]

    real_path = DATASET_DIR / "True.csv"
    fake_path = DATASET_DIR / "Fake.csv"

    with open(real_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for i in range(n_per_class):
            writer.writerow(_make_real_row(i))

    with open(fake_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for i in range(n_per_class):
            writer.writerow(_make_fake_row(i))

    print(f"Generated {n_per_class} real rows -> {real_path}")
    print(f"Generated {n_per_class} fake rows -> {fake_path}")


if __name__ == "__main__":
    generate()
