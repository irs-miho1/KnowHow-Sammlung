# EMV: Flachbandkabel, Imbalance Difference und Gleichtakt-Rückstrom

Know-how zur Kabelführung in Mehrplatinen-Geräten im Metallgehäuse (Beispiel: Laserdioden-/TEC-Controller mit Display). Schwerpunkt: Pinbelegung von Flachbandkabeln, Chassisanbindung der Platinen und Führung flach am Blech gegenüber frei im Raum.

## Inhalt

| Datei | Inhalt |
| --- | --- |
| [Flachbandkabel_gute_und_schlechte_Praxis.md](Flachbandkabel_gute_und_schlechte_Praxis.md) | Hauptdokument: Simulationen zu Pinbelegung, Höhe über Blech, Übersprechen, Chassisanbindung, Pfadbilanz |
| [Imbalance_Difference_Kabelfuehrung.md](Imbalance_Difference_Kabelfuehrung.md) | Einführung: Imbalance-Difference-Modell, Gleichtakt-Rückstrom, Checkliste |
| [innenleben3d.html](innenleben3d.html) | Drehbare 3D-Ansicht eines hypothetischen Geräteinneren, gute und schlechte Praxis (im Browser öffnen) |
| [abbildungen/](abbildungen/) | Alle Abbildungen als Vektor-PDF (für LaTeX) und PNG |
| [praesentation/folien.tex](praesentation/folien.tex) | Beamer-Gerüst, 18 Folien, für LuaLaTeX |
| [simulation/sim.py](simulation/sim.py) | Python-Skript, das alle Abbildungen und `kennzahlen.json` erzeugt |
| [docx/](docx/) | Beide Dokumente als Word-Datei |

## Kernaussagen

1. **Pinbelegung** ist der größte Hebel: Ein Signal mit nur einer GND-Ader ist ein symmetrisches Paar (h = 0,5). Mit S-G-S-G sinkt die Gleichtaktquelle um 23–27 dB und das Übersprechen auf ein benachbartes Analogsignal um rund 20 dB.
2. **Chassisanbindung direkt am Stecker** macht das Blech zum Rückleiter. Sie muss niederinduktiv sein (≤ 1 nH: mehrere Bolzen, flächiger Kontakt).
3. **Flach am Blech** gewinnt mit Anbindung in vier von fünf Kopplungspfaden: Geräteanregung gegen Umgebung −18 dB, Deckelöffnung −12 bis −27 dB, Nachbarkabel −31 dB. Ohne Anbindung ist flach am Blech dagegen schlechter als frei im Raum.

## Hinweise

- Die Zahlen stammen aus vereinfachten 2D- und Leitungsmodellen. Sie zeigen Richtung und Größenordnung, keine Messwerte. Vor Aussagen gegenüber Kunden mit HF-Stromzange am externen Kabel messen.
- Das Einführungsdokument nennt für die flache Führung einen Rückgang von h (0,4 → 0,15). Das gilt nur mit Chassisanbindung und Bezug Umgebung; das Hauptdokument (Abschnitt „Zwei Bezugssysteme für h“) ersetzt diese Aussage.
- Abbildungen neu erzeugen: `cd simulation && python3 sim.py` (benötigt numpy, scipy, matplotlib; Schrift Inter, sonst Standardschrift).
- Präsentation übersetzen: `cd praesentation && lualatex folien.tex`.
- Literaturangaben aus dem Fachwissen, nicht online nachgeprüft.
