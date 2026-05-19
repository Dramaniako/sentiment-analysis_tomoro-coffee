import pandas as pd
import re
import json
from transformers import pipeline
from tqdm import tqdm

# Enable progress bar for pandas apply functions
tqdm.pandas()

# 1. THE SLANG DICTIONARY (Kamus Alay)
# For a skripsi, you would usually load a massive CSV of 5000+ words here.
# For now, we hardcode a sample of the most common F&B review slang.
SLANG_MAP = {
    "bgt": "banget",
    "bgttt": "banget",
    "kmnsn": "kemanisan",
    "ga": "tidak",
    "gak": "tidak",
    "gk": "tidak",
    "jg": "juga",
    "krg": "kurang",
    "tp": "tapi",
    "dpt": "dapat",
    "pdhl": "padahal",
    "bs": "bisa",
    "kalo": "kalau",
    "klo": "kalau",
    "ny": "nya",
    "enak bet": "enak banget",
    "mantul": "mantap betul",
    "wkwk": "", # Remove laughing text as it confuses standard models
    "wkwkwk": "",
    "haha": ""
}

def clean_text(text):
    """Phase 1: Raw string cleaning"""
    if not isinstance(text, str):
        return ""
    
    # Lowercase everything
    text = text.lower()
    
    # Remove URLs, mentions, and hashtags (just in case we use Twitter data later)
    text = re.sub(r"http\S+|www\S+|https\S+", '', text, flags=re.MULTILINE)
    text = re.sub(r'\@\w+|\#', '', text)
    
    # Remove emojis and non-alphanumeric characters (keep basic punctuation for sentence context)
    # This regex keeps letters, numbers, spaces, and basic punctuation (, . !)
    text = re.sub(r'[^a-zA-Z0-9\s\.,!]', '', text)
    
    # Remove extra whitespaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def normalize_slang(text):
    """Phase 2: Slang to Formal Indonesian Conversion"""
    words = text.split()
    normalized_words = []
    
    for word in words:
        # Check if the word is in our dictionary (ignoring punctuation attached to it)
        clean_word = re.sub(r'[^\w\s]', '', word)
        if clean_word in SLANG_MAP:
            # Replace the word, but try to keep the original punctuation
            normalized_words.append(word.replace(clean_word, SLANG_MAP[clean_word]))
        else:
            normalized_words.append(word)
            
    return " ".join(normalized_words)

def main():
    print("🚀 Initializing NLP Pipeline...")
    
    # --- PHASE 1: DATA INGESTION ---
    print("\n📦 Loading extracted reviews...")
    data = []
    with open('tomoro_reviews.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
            
    df = pd.DataFrame(data)
    print(f"Total reviews loaded: {len(df)}")
    
    # Drop duplicates just in case our scraper missed any
    df.drop_duplicates(subset=['text'], inplace=True)
    
    # --- PHASE 2: TEXT CLEANING & NORMALIZATION ---
    print("\n🧹 Cleaning and normalizing text (Indonesian Slang Processing)...")
    df['clean_text'] = df['text'].progress_apply(clean_text)
    df['normalized_text'] = df['clean_text'].progress_apply(normalize_slang)
    
    # Remove rows that became empty after cleaning (e.g., a review that was just "⭐⭐⭐⭐⭐")
    df = df[df['normalized_text'].str.strip() != ""]
    
    # --- PHASE 3: SENTIMENT CLASSIFICATION ---
    print("\n🧠 Loading IndoBERT Sentiment Model (This may take a minute on first run)...")
    # We use a RoBERTa model specifically trained on Indonesian social media sentiment
    model_name = "w11wo/indonesian-roberta-base-sentiment-classifier"
    
    # Initialize the Hugging Face Pipeline
    # device=-1 forces it to use your CPU. If you have an NVIDIA GPU, change this to device=0 for 10x speed.
    sentiment_analyzer = pipeline("sentiment-analysis", model=model_name, tokenizer=model_name, device=-1)
    
    print("⚙️ Analyzing sentiment. Grab a coffee, this takes processing power...")
    
    def get_sentiment(text):
        try:
            # Truncate text to 512 tokens just in case someone wrote a novel
            result = sentiment_analyzer(text[:512])[0]
            return pd.Series([result['label'], result['score']])
        except Exception as e:
            return pd.Series(["ERROR", 0.0])

    # Apply the AI model to our normalized text
    df[['sentiment', 'confidence']] = df['normalized_text'].progress_apply(get_sentiment)
    
    # --- PHASE 4: DATA EXPORT ---
    print("\n💾 Exporting results to CSV...")
    # Reorder columns for readability
    export_df = df[['author', 'rating', 'text', 'normalized_text', 'sentiment', 'confidence']]
    export_df.to_csv('tomoro_sentiment_results.csv', index=False, encoding='utf-8')
    
    print(f"✅ Pipeline Complete! Check 'tomoro_sentiment_results.csv'.")
    
    # Print a quick summary of the sentiment distribution
    print("\n📊 Sentiment Summary:")
    print(df['sentiment'].value_counts())

if __name__ == "__main__":
    main()