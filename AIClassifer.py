import DB
import joblib
from sklearn.tree import DecisionTreeClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from transformers import pipeline
import string
import re
from datasets import Dataset

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

CATEGORIES = [
    "ecommerce",
    "wiki",
    "fourm",
    "blog",
    "news",
    "portfolio",
    "landing_page",
    "educational",
    "gambling",
]

def isGarbage(text, threshold=0.3):
    if not text or not isinstance(text, str):
        return True
    printable = set(string.printable)
    ratio = sum(c in printable for c in text) / len(text)
    return ratio < (1 - threshold)  # e.g. if <70% printable, reject

def isNotEnglish(text, threshold=0.2):
    # Match CJK (Chinese, Japanese, Korean) characters
    foreign_chars = re.findall(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]', text)
    return len(foreign_chars) / len(text) > threshold

def isNoiseOnly(text):
    return not any(c.isalnum() for c in text)

def isTooShort(text, min_len=30):
    return len(text.strip()) < min_len

def isValidPage(text):
    if not text: return False
    return (
        not isGarbage(text) and
        not isNotEnglish(text) and
        not isNoiseOnly(text) and
        not isTooShort(text)
    )

def ModelTrain(connection, texts, labels):
    # Filter invalid entries
    if not texts:
        print("No labeled data found!, Running auto-labeling...")
        autoGuessLabels(connection)
    cleaned = [(t, l) for t, l in zip(texts, labels) if isValidPage(t)]
    if not cleaned:
        print("No valid training data after filtering.")
        return

    texts, labels = zip(*cleaned)

    # Check if all documents are empty or useless
    if all(len(t.strip()) == 0 for t in texts):
        print("All documents are empty after stripping.")
        return

    # Convert text to TF-IDF features
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    try:
        X = vectorizer.fit_transform(texts)
    except ValueError as e:
        print("Vectorizer error:", e)
        return

    # Train decision tree
    clf = DecisionTreeClassifier()
    clf.fit(X, labels)

    # Save model and vectorizer
    joblib.dump(clf, 'model.pkl')
    joblib.dump(vectorizer, 'vectorizer.pkl')
    print("Model and vectorizer saved.")

def educatedGuess(text):
    t = text.lower()
    # Discard unhelpful pages
    if "enable javascript" in t or "turn on javascript" in t:
        return None
    # Blog
    if any(kw in t for kw in ["blog", "subscribe", "posted on", "leave a comment", "author", "archive", "read more"]):
        return "blog"
    # Ecommerce
    if any(kw in t for kw in ["cart", "checkout", "buy", "shop now", "add to cart", "wishlist", "order", "free shipping", "payment"]):
        return "ecommerce"
    # Forum
    if any(kw in t for kw in ["forum", "thread", "posts", "replies", "last post", "topic", "register to reply", "moderator"]):
        return "forum"
    # Wiki
    if any(kw in t for kw in ["wiki", "edit this page", "citation", "navigation", "categories", "reference", "read", "view source"]):
        return "wiki"
    # Portfolio
    if any(kw in t for kw in ["portfolio", "projects", "my work", "about me", "skills", "experience", "resume", "cv", "case study"]):
        return "portfolio"
    # News
    if any(kw in t for kw in ["news", "breaking", "headline", "report", "journalist", "editorial", "live update", "press", "coverage"]):
        return "news"
    # Landing Page / Marketing
    if any(kw in t for kw in ["signup", "get started", "free trial", "our product", "what we do", "contact us", "schedule a demo", "try now"]):
        return "landing_page"
    # Educational
    if any(kw in t for kw in ["course", "curriculum", "lessons", "lectures", "tutorial", "learn", "syllabus", "academic", "education"]):
        return "educational"
    # Gambling / Casino
    if any(kw in t for kw in ["gamble", "casino", "gambling", "slots", "blackjack", "roulette", "jackpot", "bet now", "winnings", "poker"]):
        return "gambling"

    return None  # Unsure

def autoGuessLabels(connection):
    pages = DB.fetchUnlabeledData(connection, limit=200)

    valid_pages = []
    educated_guesses = {}

    for page_id, text in pages:
        if not isValidPage(text):
            print(f"[Filtered] ID {page_id}: {repr(text[:50])}")
            continue
        guess = educatedGuess(text)
        if guess:
            educated_guesses[page_id] = guess
        else:
            valid_pages.append((page_id, text))
    print(f"Valid pages: {len(valid_pages)}")

    if valid_pages:
        ids, texts = zip(*valid_pages)
        results = classifier(list(texts), candidate_labels=CATEGORIES)
        for page_id, result in zip(ids, results):
            guess = result['labels'][0]
            educated_guesses[page_id] = guess

    for page_id, guess in educated_guesses.items():
        print(f"[{page_id}] → {guess}")
        DB.updateCategoryData(connection, page_id, guess)

def trainNewModel():
    connection = DB.start_db()
    texts, labels = DB.fetchTrainData(connection)
    ModelTrain(connection, texts, labels)

def runModel():
    connection = DB.start_db()
    clf = joblib.load('model.pkl')
    vectorizer = joblib.load('vectorizer.pkl')
    pages = DB.fetchUnlabeledData(connection)
    
    for page_id, page_text in pages:
        if not isValidPage(page_text):
            print(f"[Filtered] ID {page_id}: {repr(page_text[:50])}")
            continue

        vector = vectorizer.transform([page_text])
        prediction = clf.predict(vector)[0]
        DB.updateCategoryData(connection, page_id, prediction)
        print(f"Updated page ID {page_id} with category: {prediction}")

def evaluateModel():
    connection = DB.start_db()
    texts, labels = DB.fetchTrainData(connection)

    # Filter out invalid pages as before
    filtered = [(t, l) for t, l in zip(texts, labels) if isValidPage(t)]
    if not filtered:
        print("No valid labeled data to evaluate.")
        return

    texts, labels = zip(*filtered)

    # Split data: 80% train, 20% test (adjust as you like)
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts, labels, test_size=0.2, random_state=42)

    # Vectorize training texts
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    X_train = vectorizer.fit_transform(train_texts)

    # Train model
    clf = DecisionTreeClassifier()
    clf.fit(X_train, train_labels)

    # Save model and vectorizer
    joblib.dump(clf, 'model.pkl')
    joblib.dump(vectorizer, 'vectorizer.pkl')

    # Vectorize test texts using the trained vectorizer
    X_test = vectorizer.transform(test_texts)

    # Predict on test set
    preds = clf.predict(X_test)

    # Evaluate
    print("Accuracy:", accuracy_score(test_labels, preds))
    print("Classification Report:\n", classification_report(test_labels, preds))



def main():
    trainNewModel()
    evaluateModel()
    #runModel()


if __name__ == "__main__":
    main()

    