# Filter aus Drosseln und Kondensatoren unter Gleichspannung messen

Ziel: Filter (vor allem EMV-Eingangsfilter) bis ca. 50 V DC realistisch vermessen.
Verfügbare Geräte: Oszilloskop, Omicron Bode 500, LiteVNA, Siglent SSA3075X-R, Picotest Current Injector.

---

## 1. Grundlagen: Was hängt wovon ab?

- **Drosseln** reagieren auf den **DC-Strom** (Sättigung), nicht auf die Spannung. Ohne Laststrom misst man praktisch dasselbe wie ohne DC.
- Auf die **Spannung** reagieren vor allem die **Kondensatoren**. MLCCs verlieren bei hoher DC-Spannung oft einen Großteil ihrer Kapazität.
- Für realistische Werte braucht man also Spannung **und** Laststrom.

---

## 2. Einzelnes Filter / Bauteile auf dem Labortisch

### Durchgangsdämpfung (S21) mit Bias-Tees

Messung wie gewohnt in 50 Ω (Bode 500 oder LiteVNA). DC über Bias-Tees an beiden Ports:

1. Netzteil → Entkoppeldrossel → Filtereingang. An denselben Knoten ein Koppelkondensator zum Generatorausgang.
2. Filterausgang → Koppelkondensator zum Empfänger. Parallel dazu Entkoppeldrossel → elektronische Last / Lastwiderstand mit Nennstrom.
3. Fertig kaufen: Picotest J2130A (DC Bias Injector, auch für tiefe Frequenzen) oder koaxiale Bias-Tees (z. B. Mini-Circuits, meist erst ab einigen 100 kHz).
4. Selbstbau: Entkoppeldrosseln müssen im ganzen Messbereich deutlich mehr als 50 Ω haben und dürfen beim Prüfstrom nicht sättigen. Kontrolle: Aufbau mit Durchverbindung statt Filter messen und als Thru-Kalibrierung verwenden.

### Gerätewahl

| Gerät | Einsatz |
|---|---|
| Bode 500 | Erste Wahl für den EMV-Bereich (ca. 10 kHz – 30 MHz) und tiefer |
| LiteVNA | Höhere Frequenzen; empfindliche Eingänge, unbedingt DC-Blocks |
| SSA3075X-R | Mit Tracking-Generator brauchbar, kein Vorteil gegenüber Bode; ideal für Störmessungen |

### Nur die Drossel prüfen (am einfachsten)

Spannungssprung über einen MOSFET auf die Drossel, Strom mit Shunt oder Stromzange am Oszi messen.
**L = U / (di/dt)**. Ab dem Sättigungsstrom wird die Stromrampe sichtbar steiler → L über den gesamten Strombereich in einer Messung.

### Schutz der Messgeräte

- Erst verkabeln, dann DC langsam hochfahren. Vor dem Abklemmen Koppelkondensatoren entladen.
- Ladestromstöße beim Ein-/Umstecken sind der häufigste Grund für tote VNA-Eingänge.
- Begrenzer oder Dämpfungsglied (z. B. 10 dB) vor dem Empfängereingang.

### Norm

CISPR 17 beschreibt die Messung der Einfügedämpfung von Filtern, auch unter Last und mit unsymmetrischen Impedanzen (0,1 Ω / 100 Ω). Die 50-Ω-Messung beschönigt reale Filter oft.

---

## 3. Filter eingebaut in einer Gesamtschaltung (in-circuit)

Am besten **im laufenden Betrieb** messen: Die Schaltung liefert Spannung, Laststrom und echte Quell-/Lastimpedanzen.

### a) Vorhandene Störungen als Messsignal (am einfachsten)

- Mit dem Spektrumanalysator die HF-Spannung **vor und nach dem Filter** messen (Koppelkondensator mit 50-Ω-Abgriff oder Tastkopf).
- Differenz der Spektren = tatsächliche Dämpfung im Betrieb.
- Nachteil: nur bei den Frequenzen sichtbar, auf denen die Schaltung stört.

### b) Signal einspeisen, mit Bode 500 vor/nach dem Filter messen

Wie eine Loop-Gain-Messung:
- **Einspeisen** am Filtereingang über Koppelkondensator oder Injektionstrafo (z. B. Omicron B-WIT 100) in einer aufgetrennten Leitung.
- **Messen:** Kanal 1 am Eingang, Kanal 2 am Ausgang, hochohmig und DC-entkoppelt. CH2/CH1 = Übertragungsfunktion im Betrieb.

### c) Impedanz eines Knotens (Shunt-Thru)

- Bode oder LiteVNA, zwei Ports mit DC-Blocks.
- Bei sehr kleinen Impedanzen verfälscht die Masseschleife über die Kabelschirme das Ergebnis → Ferrite / Gleichtaktdrossel auf den Kabeln oder Masseschleifen-Isolator.

### Praktische Tipps

- **Abgriffe:** Kurze Koax-Pigtails direkt an die Pads löten, SMD-Kondensator in Serie als DC-Block. Massefahnen von Tastköpfen sind ab einigen MHz unbrauchbar.
- **Massebezug:** Hängt die Platine am Schutzleiter, entstehen Masseschleifen über die Messgeräte → potentialfrei betreiben.
- **Messbarkeit prüfen:** Dämpfungen über ca. 60 dB sind eingebaut kaum messbar (Überkopplung über Platine und Kabel). Kontrolle: Abgriff an Masse legen und Grundrauschen ansehen.
- **Nachrechnen:** Arbeitspunkt messen, dann mit Herstellerdaten unter DC-Bias simulieren (LTspice). Würth REDEXPERT: L über Strom; Murata SimSurfing / TDK: C über Spannung.
- **Abtrennbar machen:** Filterabschnitt per Leiterbahnschnitt oder 0-Ω-Brücke trennbar machen, oder Bauteile auf einer Testplatine nachbauen.

---

## 4. EMV-Eingangsfilter mit dem Picotest Current Injector

Misst die **Gegentakt-Dämpfung (DM) im Betrieb** mit echtem DC-Strom.

### Prinzip

Der Injektor ersetzt den Störer: Er zieht auf der Wandlerseite des Filters einen modulierten Strom zwischen Versorgungsschiene und Masse, wie der Rippelstrom des Schaltreglers. Gemessen wird, was am Netzeingang ankommt.

### Aufbau

1. Platine über eine **Netznachbildung (LISN)** versorgen (50 Ω ∥ 50 µH) → genormte Quellimpedanz, vergleichbar mit EMV-Messungen.
2. Injektor mit kurzen Leitungen an den Kondensator auf der Wandlerseite des Filters.
3. Bode 500:
   - **Ausgang** → Modulationseingang des Injektors
   - **Kanal 1** → Strommonitor-Ausgang des Injektors (Referenz)
   - **Kanal 2** → Messausgang der LISN (50 Ω, DC-frei)
4. CH2/CH1 = **Transimpedanz in dBΩ** (Störspannung an der LISN pro Ampere Störstrom).
5. Skalierungsfaktor des Strommonitors (V/A) im Bode als Referenzkorrektur hinterlegen.

### Nutzen

- **Vorhersage:** Rippelstrom des Wandlers [dBµA] + Transimpedanz [dBΩ] = Störpegel an der LISN [dBµV].
- Filtervarianten schnell vergleichen; Resonanzen und Sättigung bei Volllast fallen sofort auf.
- Wandler darf laufen: Die schmalbandige Messung blendet seine Störungen weitgehend aus (ggf. IF-Bandbreite verringern, Amplitude erhöhen).

### Grenzen

- **Nur Gegentakt.** Gleichtakt (über Y-Kondensatoren und Streukapazitäten) wird nicht erfasst → kapazitiv oder per Stromzange einkoppeln und Strom auf beiden Leitern gemeinsam messen, oder LISN + DM/CM-Trenner + Spektrumanalysator.
- **Bandbreite des Injektors** im Datenblatt prüfen; das obere Ende des Bandes (bis 30 MHz) ist oft grenzwertig.
- **Spannungs-/Stromgrenzen** des Injektors einhalten; Modulationspegel klein halten, damit der Arbeitspunkt nicht verschoben wird.

### Ergänzung: Pre-Compliance mit dem SSA3075X-R

- Mit derselben LISN leitungsgebundene Störungen messen (150 kHz – 30 MHz), Peak bzw. Quasi-Peak (falls EMI-Option vorhanden).
- **DM/CM-Trenner** zeigt, welcher Anteil überwiegt → am X- oder Y-Teil des Filters arbeiten.
- Ohne LISN (definierte Quellimpedanz) sind EMV-Filtermessungen kaum vergleichbar.
