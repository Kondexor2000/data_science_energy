# Zielona Polska — tani prąd, czyste powietrze

MVP portfolio Data Science: eksploracja produkcji energii elektrycznej w Polsce, monitorowanie udziału OZE i intensywności emisji oraz ostrożna ilustracyjna ekstrapolacja trendu. To narzędzie analityczne, nie model cen energii ani ewaluacja wpływu KPO.

## Szybki start

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
pip install -e '.[dev]'
streamlit run app.py
```

Po pierwszym uruchomieniu dane pobierane są z OWID i zapisywane w `data/processed/poland_energy.csv`. Można też wskazać `DATA_PATH`, np. `DATA_PATH=data/processed/poland_energy.csv streamlit run app.py`, aby uruchomić aplikację z lokalnym plikiem. `python -m zielona_polska.pipeline` odświeża dane i zapisuje przetworzony wyciąg.

## Docker

```bash
docker compose up --build
```

Aplikacja będzie dostępna pod `http://localhost:8501`. Wolumen `energy-data` zachowuje dane między restartami. Kontener działa jako użytkownik nieuprzywilejowany.

## GitHub Pages

Repozytorium publikuje statyczny dashboard przez workflow `.github/workflows/pages.yml`; nie wymaga bazy danych ani serwera aplikacyjnego. Przy każdym wdrożeniu GitHub Actions pobiera dane OWID, przygotowuje `docs/data/poland_energy.json` i publikuje zawartość katalogu `docs`. Włącz publikację Pages ze źródłem **GitHub Actions** w ustawieniach repozytorium. Dashboard będzie dostępny pod `https://kondexor2000.github.io/data_science_energy/`.

Statyczna wersja zawiera wskaźniki, wykres miksu, scenariusz trendu, walidację chronologiczną i wyciąg danych. Pełna aplikacja Streamlit nadal działa lokalnie lub przez Docker — GitHub Pages nie uruchamia aplikacji Python.

## Jenkins

Jenkins Pipeline oczekuje agenta z Docker CLI i dostępem do daemonu Docker. Dodaj projekt do repozytorium i skonfiguruj job typu **Pipeline** wskazujący `Jenkinsfile`. Etapy: instalacja zależności, lint, testy, budowa obrazu i smoke test kontenera. Dane pobierane są w pipeline; w środowisku offline można przekazać lokalny plik przez `DATA_PATH`.

## Zakres i metody

- Zakres: roczna produkcja energii, 1990+, Polska; hydro, wiatr, słońce, inne OZE, paliwa kopalne, łączna generacja i intensywność emisji.
- Wskaźnik OZE jest liczony jako (hydro + wiatr + słońce + inne OZE) / generacja ogółem. Brakujące składowe nie są po cichu imputowane.
- Prognoza wykorzystuje regresję liniową na udziale OZE, z ograniczeniem wyniku do 0–100%. Jest wyłącznie scenariuszem ekstrapolacyjnym: brak przedziałów ufności i przyczynowej interpretacji.
- Walidacja szeregu czasowego: porównanie MAE regresji z naiwnym baseline ostatniej obserwacji na ostatnich latach. Brak losowego podziału danych.
- Nie ma w źródle danych cen detalicznych, nakładów KPO ani kontrfaktycznego scenariusza. Nie można więc wnioskować, że OZE obniża rachunki lub że KPO spowodowało zaobserwowane zmiany.

## Źródła i ograniczenia

Dane: [OWID Energy dataset](https://catalog.ourworldindata.org/energy/owid_energy/), skompilowany z Ember, Energy Institute, EIA i innych źródeł. Zmienna intensywności emisji ma własną metodologię i może nie odpowiadać krajowym inwentaryzacjom. Dataset jest aktualizowany, więc wyniki mogą się zmieniać po odświeżeniu. Dane są agregatami rocznymi, nie odzwierciedlają cen godzinowych, jakości powietrza w lokalizacjach ani rozkładu kosztów między gospodarstwa domowe.

## Struktura

```text
app.py                 Streamlit dashboard
src/zielona_polska/    pobieranie, kontrola jakości i walidacja
tests/                 testy jednostkowe
Dockerfile             obraz aplikacji
compose.yaml           lokalne uruchomienie
Jenkinsfile            CI/CD
```

## Rozwój

```bash
ruff check .
pytest
```

W produkcji przypnij wersje zależności i bazowy obraz do digestu, dodaj monitoring świeżości danych oraz testy kontraktowe po zmianach schematu źródła.
