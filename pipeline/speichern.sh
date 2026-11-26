#!/usr/bin/env bash
# Speichert die Ergebnisse eines Datenlaufs im Repo (Schritt "Änderungen speichern" in daten.yml).
# Liegt inzwischen ein anderer Commit auf main, wird zuerst abgeglichen. Gibt es dabei einen Konflikt in den erzeugten
# Dateien (z. B. weil parallel an der Seite gebaut wurde), wird nicht weiter versucht, denselben Konflikt aufzulösen:
# Der Lauf übernimmt seine Rohdaten (data/), setzt auf den neuesten Stand von main auf und rechnet die erzeugten Dateien
# (site/data, Feed, Startseite, Berichte, Sitemap) damit neu. Telegram wurde vorher schon gesendet und wird nicht wiederholt.
set -u
PFADE="data site/data site/feed.xml site/index.html site/RULES.md site/LICENSE site/en site/bericht site/audit site/sitemap.xml"

git config user.name "cyberlage-bot"
git config user.email "cyberlage-bot@users.noreply.github.com"
git add $PFADE
git diff --cached --quiet && exit 0
git commit -q -m "Daten aktualisiert"

for i in 1 2 3; do
  git fetch -q origin main || { echo "Versuch $i: Abruf fehlgeschlagen"; sleep 5; continue; }
  if git rebase -q origin/main 2>/dev/null; then
    git push -q origin HEAD:main && exit 0
    echo "Versuch $i: Push abgelehnt, neuer Versuch"; sleep 5; continue
  fi
  echo "Versuch $i: Konflikt, rechne auf dem neuesten Stand neu"
  git rebase --abort
  bot=$(git rev-parse HEAD)
  git diff --name-only "$bot^" "$bot" -- data > "${RUNNER_TEMP:-/tmp}/bot_daten.txt"
  git reset -q --hard origin/main
  while IFS= read -r f; do git checkout "$bot" -- "$f" || exit 1; done < "${RUNNER_TEMP:-/tmp}/bot_daten.txt"
  git checkout origin/main -- data/logbuch.json 2>/dev/null || true   # von Hand gepflegt, der Lauf ergänzt nur Ereignisse
  python pipeline/score.py && python pipeline/feed.py && python pipeline/prerender.py || exit 1
  git add $PFADE
  git diff --cached --quiet && exit 0
  git commit -q -m "Daten aktualisiert (nach Abgleich neu gerechnet)"
  git push -q origin HEAD:main && exit 0
  echo "Versuch $i: Push abgelehnt, neuer Versuch"; sleep 5
done
exit 1
