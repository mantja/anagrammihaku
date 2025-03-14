from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, text
from itertools import combinations
import re
from dotenv import load_dotenv
import os

app = FastAPI()

# 🔹 **MariaDB-yhteys**
load_dotenv()  # Lataa .env-tiedoston muuttujat

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = "sanat"
DB_PORT = os.getenv("DB_PORT")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)


# 🔹 **Poistetaan erikoismerkit ja välilyönnit, mutta säilytetään skandinaaviset kirjaimet**
def clean_word(word: str) -> str:
    """ Poistaa erikoismerkit ja välilyönnit, mutta säilyttää suomen kielen kirjaimet """
    return re.sub(r"[^a-zA-ZäöåÄÖÅ]", "", word)


# 🔹 **Tarkistaa, löytyykö sana tietokannasta**
@app.get("/check/{word}")
def check_word_exists(word: str):
    word = clean_word(word)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM words WHERE word = :word"), {"word": word})
        count = result.scalar()

    return {"word": word, "exists": count > 0}
    

# 🔹 **Anagrammihaku ja sanayhdistelmien etsiminen**
@app.get("/anagram/{word}")
def find_anagrams(word: str):
    word = clean_word(word)
    sorted_input = "".join(sorted(word))

    with engine.connect() as conn:
        # 🔹 **Haetaan täydelliset anagrammit**
        result = conn.execute(
            text("SELECT word FROM words WHERE sorted_word = :sorted_input AND word != :original_word"),
            {"sorted_input": sorted_input, "original_word": word}
        )
        anagrams = [row[0] for row in result.fetchall()]

        # 🔹 **Haetaan kaikki sanat ja tallennetaan sorted_word -> alkuperäinen sana**
        result = conn.execute(text("SELECT word, sorted_word FROM words"))
        all_words = {row[1]: row[0] for row in result.fetchall()}  # `{sorted_word: word}`

    # 🔹 **Jos täydellisiä anagrammeja ei löydy, etsitään sanapareja ja kolmiosia**
    word_combinations = find_word_combinations(word, all_words) if not anagrams else []

    return {
        "word": word,
        "anagrams": anagrams if anagrams else [],
        "split_anagrams": word_combinations if word_combinations else [],
        "message": "Ei löydetty anagrammeja." if not anagrams and not word_combinations else ""
    }


# 🔹 **Etsitään kaikki mahdolliset kahden tai kolmen sanan yhdistelmät**
def find_word_combinations(word: str, word_list: dict):
    valid_combinations = []

    def score_combination(parts):
        """ Pisteytys suosii pidempiä ja tasapainoisia sanoja """
        return sum(len(p) for p in parts) + min(len(p) for p in parts) * 2

    word_sorted = "".join(sorted(word))  # Lajitellaan sana aakkosjärjestykseen

    # 🔹 **Kahden sanan yhdistelmät**
    for i in range(1, len(word) - 1):
        for combo in combinations(word, i):
            part1 = "".join(sorted(combo))
            part2 = "".join(sorted(set(word) - set(combo)))

            if part1 in word_list and part2 in word_list:
                words = sorted([word_list[part1], word_list[part2]])

                if "".join(sorted("".join(words))) == word_sorted:
                    valid_combinations.append((words, score_combination(words)))

    # 🔹 **Kolmen sanan yhdistelmät**
    for i in range(1, len(word) - 2):
        for j in range(i + 1, len(word) - 1):
            for combo1 in combinations(word, i):
                remaining1 = set(word) - set(combo1)

                for combo2 in combinations(remaining1, j - i):
                    part1 = "".join(sorted(combo1))
                    part2 = "".join(sorted(combo2))
                    part3 = "".join(sorted(remaining1 - set(combo2)))

                    if part1 in word_list and part2 in word_list and part3 in word_list:
                        words = sorted([word_list[part1], word_list[part2], word_list[part3]])

                        if "".join(sorted("".join(words))) == word_sorted:
                            valid_combinations.append((words, score_combination(words)))

    valid_combinations.sort(key=lambda x: x[1], reverse=True)

    return [combo[0] for combo in valid_combinations]


# 🔹 **HTML-käyttöliittymä**
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """ HTML-käyttöliittymä anagrammien hakuun ja sanan tarkistukseen """
    return """
    <!DOCTYPE html>
    <html lang="fi">
    <head>
        <meta charset="UTF-8">
        <title>Anagrammihaku</title>
        <script>
            async function fetchAnagram() {
                let word = document.getElementById("wordInput").value;
                let response = await fetch("/anagram/" + word);
                let data = await response.json();
                
                let resultHTML = "<h3>Tulokset:</h3>";
                if (data.anagrams && data.anagrams.length > 0) {
                    resultHTML += "<p><strong>Anagrammit:</strong> " + data.anagrams.join(", ") + "</p>";
                } 
                if (data.split_anagrams && data.split_anagrams.length > 0) {
                    resultHTML += "<p><strong>Sanayhdistelmät:</strong><br>";
                    data.split_anagrams.forEach(combo => {
                        resultHTML += "- " + combo.join(" + ") + "<br>";
                    });
                    resultHTML += "</p>";
                }
                if (!data.anagrams.length && !data.split_anagrams.length) {
                    resultHTML += "<p>Ei löydetty anagrammeja.</p>";
                }
                
                document.getElementById("results").innerHTML = resultHTML;
            }

            async function checkWord() {
                let word = document.getElementById("checkInput").value;
                let response = await fetch("/check/" + word);
                let data = await response.json();
                let checkResult = document.getElementById("checkResult");
                checkResult.innerHTML = data.exists ? `<p style='color: green;'>${word} löytyy sanastosta!</p>` : `<p style='color: red;'>${word} ei löytynyt sanastosta.</p>`;
            }
        </script>
    </head>
    <body>
        <h1>Anagrammihaku</h1>
        <input id="wordInput"><button onclick="fetchAnagram()">Hae</button>
        <div id="results"></div>
        <h1>Sanan tarkistus</h1>
        <input id="checkInput"><button onclick="checkWord()">Tarkista</button>
        <div id="checkResult"></div>
    </body>
    </html>
    """
