# FM08 Extended — features in English

[Project](README.md) · [Installation](INSTALLATION.md#english) ·
[Full documentation, Polish](DOCUMENTATION.md) · [Polski](PL.md)

FM08 Extended launches Football Manager 2008 with selected extensions.
It does not replace the game or its database. Native engine integrations
are **experimental** — use a copy of your career for initial testing.

## Feature index

- [Launching and settings](#launching)
- [Interface, language and theme](#interface)
- [Advanced mode](#advanced)
- [Display](#display)
- [Substitutions and substitutes bench](#rules)
- [Dynamic player potential](#pa)
- [Delayed aging](#aging)
- [Additional player information](#panels)
- [Skin installer](#skins)
- [Dynamic league reputation and profiles](#reputation)
- [Read-only league observation](#observation)
- [Diagnostics and logs](#diagnostics)
- [Community and support](#community)
- [Limitations and planned features](#limitations)

<a id="launching"></a>
## Launching and settings

- Select `fm.exe`; the launcher also tries to locate it in parent folders.
- Optionally select your FM08 user data folder containing skins, graphics
  and saves. This is not the installation's `data` folder. Selecting it
  does not move files or change where FM08 saves careers.
- **PLAY** validates settings, asks for confirmation, saves the configuration
  and starts the game. There is no need to press Save first.
- Cancelling confirmation does not save edits; validation or save errors
  block launching.
- Settings are loaded the next time the launcher starts.
  Manual **Save / Reload** are available in advanced mode and concern
  launcher settings, not FM08 career saves.
- Changing switches during a game does not reconfigure that session.
  New integrations require restarting the game through the launcher.

Requires Windows x64, .NET 8 Desktop Runtime x64 and a supported FM08 8.0.2
executable. Integrations verify the full SHA256 and original instructions.
Accepted files: [compatibility](DOCUMENTATION.md#1-wymagania-i-zgodnosc).

<a id="interface"></a>
## Interface, language and theme

- Two tabs: **Home** and **Skins**.
- Feature cards have independent ON/OFF switches.
- **Details** reveals descriptions and controls without enabling a feature.
- Switch between Polish and English without restarting or losing edits.
  The launcher's language does not change FM08's own language.
- Light and dark themes cover the main interface and report windows.
  System dialogs remain controlled by Windows.
- Display mode and resolution controls stay visible.
- PLAY stays at the bottom; career profile status appears when actual
  league reputation changes are enabled.

New in-game panel text uses the language selected when the game starts.
Changing that text in an existing session requires restarting the game.

<a id="advanced"></a>
## Advanced mode

Default player mode hides technical tools: league observation and
diagnostics, PA counters/logs, reputation change logs and manual Save/Reload.
Advanced mode makes them available.

**Hiding a tool does not disable it.** If hidden observation or diagnostics
remain enabled, the launcher displays a warning. Skin instructions and XML,
match settings and career profile controls remain available in player mode.

<a id="display"></a>
## Display

- **Window:** fixed resolution, frame, title bar and minimization.
- **Borderless window:** selected size centered on the primary screen,
  without stretching or changing desktop resolution.
- **Fullscreen:** FM08's native mode; further manual verification is needed.
- Detect available primary-monitor resolutions within
  **640 × 480–1920 × 1080**, accounting for desktop bounds, frame and DPI.
- Verify actual window and rendering-buffer dimensions during startup.
- OFF preserves the game's original behavior.

Compatibility with every skin or monitor arrangement is not guaranteed.

<a id="rules"></a>
## Substitutions and substitutes bench

- Configure substitutions and bench size independently.
- Separate overrides for **29 rule codes, 0–28**.
- Active range **0–12**; edit the table or use the arrow controls below it.
- Sort columns in either direction, with numeric sorting for numbers.
- The master OFF switch skips overrides while preserving their settings.
- Disabled overrides preserve original rules, including conditional limits.
- Competition examples help identify codes but are not a complete league map.

A rule code **does not select a single league**. Multiple competitions and
stages may share it. The current map contains 45 assignments across 15 codes;
the remaining codes have an unidentified scope. An override also affects
unlisted matches using that code.

The 0–12 range does not guarantee every combination is safe; actual match
testing is required. Available substitutes may limit usable substitutions.
Extra time, friendlies and youth teams require separate verification.

<a id="pa"></a>
## Dynamic player potential

Optional **PA** growth, independent of displaying information in panels.
Applies to all eligible players, not only your own club.

- Eligibility: CA/PA 1–200, PA below 200 and a PA−CA gap of 0–4.
- At most one roll at a new native weekly training update.
- Success gives **+1 PA**, without directly increasing CA.
- Base probability: **8%**, modified by age and mentality.
- Mentality weights: professionalism 60%, ambition 25%, determination 15%.
- Age multipliers: up to 18: 1.25; 19–21: 1.10; 22–24: 1.00;
  25–27: 0.70; 28–30: 0.40; 31–33: 0.15; 34+: 0.05.
- Maximum PA: 200. No seasonal allowance or +5 seasonal cap.
- Refreshing panels does not create additional rolls.
- No increase in a particular week is a valid random outcome.

Example: an 18-year-old with professionalism, ambition and determination
all at 20 has a 15% chance in an eligible week.
Full formula: [PA model](DOCUMENTATION.md#6-dynamiczne-pa).

Advanced mode provides counters and a journal containing the player,
CA, PA before/after and update number. The journal is session-only,
not written to disk, and can report lost entries. Growth itself continues
after closing the launcher. Saving a career persists earned PA;
turning the feature off does not reverse previous increases.

<a id="aging"></a>
## Delayed aging

An independent, default-OFF module shifts effective physical-decline
thresholds and age-related CA penalties by **3 years**, preserving
individual player factors.

It does not change birth dates, displayed age, youth development or
retirement decisions. It does not guarantee a longer career for any player.
Development effects may persist through career saves.

<a id="panels"></a>
## Additional player information

- **Training:** seasonal fatigue and an explanatory tooltip.
- **Squad / Selection:** fatigue and numeric CA and PA.
- **Tactics / Position:** fatigue alongside condition.
- An additional compact **Edycja** view, without removing existing views.

Information is restricted to the active human manager's club, its actual
reserves/U23 and players loaned into the club. Separate affiliates,
national teams, other clubs' players and outgoing loanees are excluded.
Unavailable or unauthorized information displays `----`.

Seasonal fatigue is not condition. Categories: rested (J ≤ 0),
normal (1–250), increasing (251–374), high (375–499),
very high (≥ 500). The tooltip describes an effect on one training
multiplier, not overall training efficiency or injury risk.

Requires both the enabled native module and correct skin XML.
Occasionally switching views is needed to refresh fatigue descriptions.
These panels do not change CA, PA or fatigue values.

<a id="skins"></a>
## Skin installer

- Supports Steklo Black and Steklo Black (Left).
- Creates a loose override of the default `fm2008` skin.
- Preserves inheritance and existing columns.
- Backs up modified existing files with `.before-fmext-panels`.
- Does not modify FMF archives.
- Provides four XML fragments for manual integration into custom skins.

**The current installer requires at least one recognized Steklo variant
in the selected `skins` folder.** It is not a universal installer for
arbitrary skins.

Install with the game closed. Then disable skin caching in FM08,
reload the skin and select the added view. Back up your skin beforehand;
there is no automatic uninstall button.
Details: [panels and installation](DOCUMENTATION.md#8-panele-zawodnikow-i-skorki).

<a id="reputation"></a>
## Dynamic league reputation and profiles

Optional **actual reputation changes for 42 European top divisions**,
based on changes in the nation's five-year coefficient.

- A baseline profile is associated with the career, not its save filename.
- New career: the launcher creates a profile after a successful save
  once it has captured the baseline.
- Loaded career: automatically matches a compatible profile; if none exists,
  a baseline may be created from the current state.
- Manual profile import/selection and retry detection are available.
- Profiles are stored in `profils` beside the application. Keep them with
  your career backups.
- Changes occur on 15 June every two years from the baseline season.
- Each league moves at most **±1 reputation point** per eligible event.
- Normal FM08 career saves persist the changes.
- Profile status appears above PLAY; advanced mode exposes the change log.

**Keep the launcher open.** Closing it disarms the writer. Do not recreate
profiles each season. Multiple matching profiles require selection;
activation on 15 June and rewinding before the baseline are blocked.

The module does not change UEFA coefficients, qualification places or
lower divisions. Missed events are not applied retroactively.
Full model and profile rules:
[league reputation](DOCUMENTATION.md#9-rzeczywista-reputacja-lig).

<a id="observation"></a>
## Read-only league observation

A separate advanced tool reads reputations and coefficients, compares
them with a baseline and produces a **simulation**, without changing
the game. It can read an already-running supported FM08 process.

Shows actual/baseline reputations, coefficients, the model target,
simulated reputation and annual confirmations. This older simulation
requires two consecutive same-direction annual assessments for a ±1 step;
that is not the actual writer's rule. JSON reports remain in
`league-observations`. Create a new confirmed baseline after loading a save
or changing the game process.

<a id="diagnostics"></a>
## Diagnostics and logs

Advanced mode provides:

- a session-only PA growth journal;
- persistent actual reputation change logs (`league-changes`);
- read-only observation reports (`league-observations`);
- native annual UEFA history and loader diagnostics (`league-diagnostics`).

Separate diagnostics require launching the game through the launcher and
do not themselves change reputation. The actual change module also installs
diagnostics for its own lifecycle checks. Errors and lost records are
reported. Logs do not replace career saves; a missing entry does not prove
an event never happened.

<a id="community"></a>
## Community and support

- [YouTube](https://www.youtube.com/@Bezimienny111)
- [Discord](https://discord.gg/hP2g4MQS5T)
- [Ko-fi — support the project](https://ko-fi.com/ericaaurora)

Please include **FM08Extended** in your support message.
The application's Git icon remains inactive until a repository URL is set.

<a id="limitations"></a>
## Limitations and planned features

The launcher does not modify the game EXE on disk. Hooks live in the
new game's process memory; gameplay effects can nevertheless persist
in career saves. Other executables, every skin, all rule combinations
and multiplayer compatibility are not guaranteed. Long career tests
are still needed.

**Not implemented yet:** database downloading and automatic updates,
a universal skin installer, position-based attribute highlighting,
a new hidden-attributes panel, Genie Scout positional ratings,
and prize-money or sponsorship modifiers.

Requirements, configuration, testing and troubleshooting:
[full technical documentation, Polish](DOCUMENTATION.md).
