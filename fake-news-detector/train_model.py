"""
train_model.py

End-to-end training pipeline for the Fake News Detector.

    Fake.csv + True.csv
          |
          v
    preprocessing (utils.clean_text)
          |
          v
    TF-IDF vectorization
          |
          v
    train: Logistic Regression, Multinomial Naive Bayes,
           Random Forest, Passive Aggressive Classifier
          |
          v
    compare accuracy on a held-out test split
          |
          v
    save the BEST model -> model/model.pkl
    save the vectorizer  -> model/vectorizer.pkl
    save metadata        -> model/metadata.pkl

Run with:
    python train_model.py

If dataset/Fake.csv / dataset/True.csv are missing, a synthetic
bootstrap dataset is generated automatically so the pipeline always
runs end-to-end. Swap in the real ISOT dataset for production accuracy
(see dataset/generate_sample_dataset.py for details).
"""

import os
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, PassiveAggressiveClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB

from config import Config
from utils import clean_text

RANDOM_STATE = 42


def load_dataset() -> pd.DataFrame:
    if not (os.path.exists(Config.TRUE_CSV) and os.path.exists(Config.FAKE_CSV)):
        print("dataset/Fake.csv or dataset/True.csv not found -- generating a bootstrap dataset...")
        from dataset.generate_sample_dataset import generate
        generate()

    true_df = pd.read_csv(Config.TRUE_CSV)
    fake_df = pd.read_csv(Config.FAKE_CSV)

    true_df["label"] = "REAL"
    fake_df["label"] = "FAKE"

    df = pd.concat([true_df, fake_df], ignore_index=True)

    # Combine title + text into a single field for vectorization, tolerating
    # datasets that only have one of the two columns.
    for col in ("title", "text"):
        if col not in df.columns:
            df[col] = ""
    df["title"] = df["title"].fillna("")
    df["text"] = df["text"].fillna("")
    df["content"] = (df["title"] + " " + df["text"]).str.strip()
    df = df[df["content"].str.len() > 0].reset_index(drop=True)

    df = df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)  # shuffle
    return df[["title", "content", "label"]]


def main():
    print("=" * 70)
    print("FAKE NEWS DETECTOR -- MODEL TRAINING PIPELINE")
    print("=" * 70)

    t0 = time.time()

    print("\n[1/5] Loading dataset...")
    df = load_dataset()
    print(f"    Loaded {len(df)} rows -> REAL: {(df['label'] == 'REAL').sum()}, "
          f"FAKE: {(df['label'] == 'FAKE').sum()}")

    print("\n[2/5] Preprocessing text (lowercase, strip punctuation, "
          "remove stopwords, lemmatize)...")
    df["clean_content"] = df["content"].apply(clean_text)
    df = df[df["clean_content"].str.len() > 0].reset_index(drop=True)
    print(f"    {len(df)} rows remain after cleaning.")

    print("\n[3/5] Splitting train/test and vectorizing with TF-IDF...")
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        df["clean_content"], df["label"],
        test_size=0.2, random_state=RANDOM_STATE, stratify=df["label"],
    )

    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=2)
    X_train = vectorizer.fit_transform(X_train_raw)
    X_test = vectorizer.transform(X_test_raw)
    print(f"    Vocabulary size: {len(vectorizer.vocabulary_)}")

    print("\n[4/5] Training and comparing candidate models...")
    candidates = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
        "Naive Bayes": MultinomialNB(),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, max_depth=None, random_state=RANDOM_STATE, n_jobs=-1
        ),
        "Passive Aggressive": PassiveAggressiveClassifier(max_iter=1000, random_state=RANDOM_STATE),
    }

    results = {}
    trained_models = {}
    for name, model in candidates.items():
        start = time.time()
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        results[name] = acc
        trained_models[name] = model
        elapsed = time.time() - start
        print(f"    {name:<22} accuracy = {acc * 100:6.2f}%   ({elapsed:.2f}s)")

    best_name = max(results, key=results.get)
    best_model = trained_models[best_name]
    best_acc = results[best_name]

    print(f"\n    >>> Best model: {best_name} ({best_acc * 100:.2f}% accuracy)")
    print("\n    Classification report for the best model:")
    print(classification_report(y_test, best_model.predict(X_test), target_names=["FAKE", "REAL"]))

    print("\n[5/5] Saving model artifacts...")
    os.makedirs(Config.MODEL_DIR, exist_ok=True)
    joblib.dump(best_model, Config.MODEL_PATH)
    joblib.dump(vectorizer, Config.VECTORIZER_PATH)

    metadata = {
        "best_model_name": best_name,
        "accuracy": best_acc,
        "all_results": results,
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "train_size": X_train.shape[0],
        "test_size": X_test.shape[0],
        "vocab_size": len(vectorizer.vocabulary_),
        # PassiveAggressiveClassifier and (rarely) others may lack predict_proba;
        # the prediction pipeline needs to know whether to use decision_function.
        "supports_proba": hasattr(best_model, "predict_proba"),
    }
    joblib.dump(metadata, Config.METADATA_PATH)

    print(f"    Saved -> {Config.MODEL_PATH}")
    print(f"    Saved -> {Config.VECTORIZER_PATH}")
    print(f"    Saved -> {Config.METADATA_PATH}")

    print(f"\nDone in {time.time() - t0:.1f}s. You can now run:  python app.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
