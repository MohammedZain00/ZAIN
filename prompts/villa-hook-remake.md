# Villa Hook — Remake Prompt Pack (9.1s / 9:16)

Source reference: 1080x1920, 30fps, 9.13s, 7 shots.
Detected cuts (s): 1.733 / 2.133 / 3.133 / 4.233 / 5.667 / 8.233

## 1. Original shot map

| # | In–Out | Dur | Content |
|---|--------|-----|---------|
| S1 | 0.00–1.73 | 1.73s | Ground-level macro on feet at the kerb edge (original: red polka dress + heeled sandals walking), tree-lined avenue, golden hour. Vehicle enters frame right at ~1.35s |
| S2 | 1.73–2.13 | 0.40s | Extreme macro: vintage car wheel spinning, dust kick |
| S3 | 2.13–3.13 | 1.00s | Macro on car bonnet + strapped wicker picnic baskets; a lemon is dislodged |
| S4 | 3.13–4.23 | 1.10s | Lemon lands on asphalt and rolls; car recedes down the avenue |
| S5 | 4.23–5.67 | 1.44s | Lemon rolls into a paved piazza; two pigeons scatter |
| S6 | 5.67–8.23 | 2.56s | Lemon rolls under a café table between men's legs, settles at the table base; camera tilts up through chair legs |
| S7 | 8.23–9.13 | 0.90s | Reveal: elderly man playing cards at the café table |

Structural DNA: a single object relay told entirely from ground level, macro + shallow DOF, each shot handing the object to the next, ending on a human reveal.

## 2. Element mapping (remake)

| Original | Remake |
|---|---|
| Red polka-dot short dress | Crisp white Saudi thobe on a young man (the groom) |
| Heeled sandals | Polished black patent-leather formal wedding oxfords |
| Vintage red car | Red sports motorcycle (superbike), rider in black leathers + black helmet, face never seen |
| Car passes the kerb | He steps off the kerb, a red bike bears down, he snaps his foot back and it rips past |
| Lemon falls from basket | Ignition key (brushed steel + slim tan leather fob) jolts free |
| Lemon rolls across piazza | Key tumbles down a flight of stone steps into the villa forecourt |
| Pigeons | Two grey doves |
| Café table legs | Wide travertine paving, warm light spill from the villa glazing |
| Reveal: old man with cards | Reveal: the villa hero frame — the SAME man in the white thobe, now seated on the entrance step |

## 3. Global style bible (prepend to every prompt)

```
Cinematic vertical 9:16, shot on ARRI Alexa with vintage anamorphic primes, T1.4,
extremely shallow depth of field, camera at ground level, warm golden-hour rolling
into blue hour, soft atmospheric haze, natural motion blur, fine 35mm grain,
palette of sand beige, travertine cream, matte black and deep charcoal,
high-end real-estate commercial look, photoreal, no stylization.
```

## 4. Negative prompt (paste into Seedance's negative field, all generations)

```
no logo, no brand mark, no watermark, no text, no captions, no subtitles, no signage,
text, letters, captions, subtitles, watermark, logo, brand mark, signage, license plate,
face visible in the opening shot, distorted feet, warped shoes, extra limbs, morphing thobe,
rider's face, camera shake, jitter, zoom, speed ramp, cartoon, 3D render, plastic skin,
oversaturation, HDR halo, harsh midday sun, crowd, parked cars in the courtyard
```

## 5. Shot-by-shot — image prompts + Seedance 2.5 motion prompts

Seedance 2.5 will not generate under 4 seconds, and every shot here is shorter than that.
So every motion prompt below is written as a **full 4-second generation** with the beat
placed deliberately inside it, and a **usable window** you trim to in the edit. Set the
generation to 4s / 9:16 / 1080p / 30fps.

Seedance reads a single flowing paragraph better than a bullet list, and it wants the order:
camera position → subject → action in time order → environment → light → style. Keep all
negatives out of the prompt itself and put them in the negative field (section 4).

### S1 — 0.00 → 1.73 (1.73s)
IMAGE (first frame)
```
Extreme close-up, camera lying flat on the road surface just below kerb height, lens
almost touching the asphalt, looking up along the kerb line. Sharp in frame: the feet of a
young Saudi man standing at the very edge of a raised pale stone kerb — glossy black
patent-leather wedding oxfords with a mirror shine, long black dress socks, and the crisp
white hem of a pressed Saudi thobe falling just far enough to cover the top of the shoes,
breaking softly over the laces. His right toe rests on the rounded lip of the kerb. Beyond
him: an upscale modern residential street at golden hour — pale concrete pavement, young
palms and ficus throwing long shadows, blurred white cubic villas with black-framed glazing
dissolving into creamy bokeh. Low warm sun rakes across the asphalt; fine dust and grit
catch the light in the foreground. Shallow depth of field T1.4, anamorphic vertical 9:16,
warm cinematic grade, 35mm grain, photoreal.
```
MOTION — Seedance 2.5, 4s generation
```
Static extreme low-angle macro shot, camera locked flat on the asphalt at kerb height. A
young Saudi man in a crisp white thobe and polished black patent-leather wedding oxfords
stands at the kerb edge. In the first second he shifts his weight and his right shoe lowers
off the kerb toward the road, the white hem swinging forward with it. At two seconds a red
sports motorcycle enters fast from the right; he snaps his right foot back up onto the kerb
and the bike rips across the foreground left to right in heavy motion blur, kicking dust and
heat haze past the lens. He settles, both shoes back on the stone. Golden hour side light,
long shadows, shallow depth of field, anamorphic vertical 9:16, natural motion blur, 35mm
film grain. The camera does not move.
```
Usable window: **0.6s – 2.4s** → trim to 1.73s.

### S2 — 1.73 → 2.13 (0.40s)
IMAGE (first frame)
```
Extreme macro at ground level: the front tire of a red sports motorcycle leaned
hard over mid-corner, rubber compressed and edge-worn, warm dust and grit lifting off the
asphalt, glossy red fairing edge and inverted fork leg catching a low gold flare, background dissolved into creamy
bokeh of a tree-lined street.
```
MOTION — Seedance 2.5, 4s generation
```
Extreme macro shot, camera planted on the asphalt. The front tire of a red sports
motorcycle leans hard over mid-corner directly in front of the lens, rubber compressed on
the edge, glossy red fairing and chrome fork leg catching a low gold flare. The bike leans
further and whips past camera-left, throwing grit and heat haze into the lens in violent
horizontal motion blur; the frame then settles on empty sunlit asphalt with dust drifting
through the light. Golden hour, shallow depth of field, anamorphic vertical 9:16, natural
motion blur, 35mm film grain. The camera stays locked on the ground.
```
Usable window: **0.8s – 1.2s** → trim to 0.40s.

### S3 — 2.13 → 3.13 (1.00s)
IMAGE (first frame)
```
Tight macro on the motorcycle's ignition barrel and glossy red fuel tank at speed. A
single brushed-steel key on a slim tan leather fob hangs from the ignition, vibrating.
The red tank mirrors the smeared street; chrome bar-end and low sun flare; everything beyond
the tank is liquid bokeh.
```
MOTION — Seedance 2.5, 4s generation
```
Tight macro shot tracking alongside a red sports motorcycle at speed, locked on the
ignition barrel and glossy red fuel tank. A single brushed-steel key on a slim tan leather
fob hangs from the ignition, vibrating. The bike snaps into a hard lean away from the kerb;
the key jolts free, lifts, turns once catching a bright specular glint, and tumbles out of
the bottom of frame in slow motion. The background rips past in continuous horizontal motion
blur. Golden hour, shallow depth of field, anamorphic vertical 9:16, 35mm film grain. The
camera tracks with the bike at constant speed.
```
Usable window: **1.0s – 2.0s** → trim to 1.00s.

### S4 — 3.13 → 4.23 (1.10s)
IMAGE (first frame)
```
Ground-level shot along a pale concrete kerb line. The brushed-steel key with its tan
leather fob lies sharp in the foreground on warm asphalt; far down the tree-lined avenue
the red sports motorcycle is a small receding shape, its tail light a red pinprick in the dusk haze, long
shadows striping the road.
```
MOTION — Seedance 2.5, 4s generation
```
Static low shot, camera resting on the road surface along a pale concrete kerb line. A
brushed-steel key on a tan leather fob drops into frame, bounces once off the warm asphalt,
spins flat with a ringing wobble and skitters toward the kerb, coming to rest. Far behind it
down the tree-lined avenue a red sports motorcycle recedes and disappears, its tail light a
red pinprick in the dusk haze. Focus racks slowly from the key to the departing bike and
back to the key. Golden hour falling toward dusk, long shadows, shallow depth of field,
anamorphic vertical 9:16, 35mm film grain. The camera does not move.
```
Usable window: **0.4s – 1.5s** → trim to 1.10s.

### S5 — 4.23 → 5.67 (1.44s)
IMAGE (first frame)
```
Low ground-level view at the top of a shallow flight of pale limestone steps that drop
from the pavement into a modern villa's forecourt. The brushed-steel key sits at the edge
of the top step; two grey doves stand in a warm pool of spill light on the stone; blue-hour
sky, the white cubic villa softly out of focus beyond.
```
MOTION — Seedance 2.5, 4s generation
```
Low ground-level shot at the top of a shallow flight of pale limestone steps dropping from
the pavement into a modern villa forecourt. Two grey doves stand in a warm pool of spill
light on the stone. A brushed-steel key on a tan leather fob slides in from frame right,
goes over the edge and tumbles down the steps, bouncing tread to tread. The doves startle
and burst upward out of frame in a flutter of wings. The camera pushes in slowly, staying
low, following the key down. Blue hour, warm window light spilling from the right, shallow
depth of field, anamorphic vertical 9:16, natural motion blur, 35mm film grain.
```
Usable window: **0.5s – 2.0s** → trim to 1.44s.

### S6 — 5.67 → 8.23 (2.56s)
IMAGE (first frame)
```
Ground-level tracking macro across a vast pale travertine-paved courtyard at blue hour.
The brushed-steel key with tan leather fob rolls across the wide joint lines of the stone.
Warm interior light spills from tall black-framed floor-to-ceiling glazing onto the
paving; a modern white cubic villa looms soft and out of focus in the background.
```
MOTION — Seedance 2.5, 4s generation
```
Ground-level tracking shot across a wide travertine-paved courtyard at blue hour. A
brushed-steel key on a tan leather fob rolls across the broad joint lines of the pale stone.
The camera tracks backward at ground level, staying locked with the rolling key, while warm
interior light from tall black-framed glazing sweeps across the metal as it passes. The key
slows, wobbles and settles flat on the stone. The camera then begins to crane and tilt
slowly upward off the paving toward a modern white cubic villa glowing soft and out of focus
in the background. Blue hour, shallow depth of field, anamorphic vertical 9:16, 35mm film
grain.
```
Usable window: **0.3s – 2.9s** → trim to 2.56s.

### S7 — 8.23 → 9.13 (0.90s) — REVEAL / HANDOFF FRAME
IMAGE (first frame)
```
Wide low-angle exterior of a modern two-storey white villa at dusk. Crisp white cubic
volumes, a tall dark-stone accent panel on the left elevation, black-framed floor-to-
ceiling glazing glowing warm gold, recessed downlights washing the soffits, a cantilevered
upper mass over a deep entrance recess. Pale limestone paved courtyard in the foreground
with wide joint lines, soft blue twilight sky above. The same young Saudi man from the
opening shot — crisp white thobe, red-and-white shemagh, polished black wedding oxfords —
sits relaxed on the entrance step. Camera very low, near ground, wide lens, clean
symmetry. No text, no logo, no signage anywhere in frame.
```
MOTION — Seedance 2.5, 4s generation
```
Wide low-angle exterior shot of a modern two-storey white villa at dusk, camera near the
ground on pale limestone paving. The camera cranes up off the paving and settles into a
locked wide composition of the villa: white cubic volumes, a tall dark-stone accent panel on
the left elevation, black-framed floor-to-ceiling glazing glowing warm gold, recessed
downlights washing the soffits. A young Saudi man in a crisp white thobe and red-and-white
shemagh sits on the entrance step; he looks up from his phone toward the fallen key and
gives a faint smile. The interior lights bloom one beat brighter across the glazing. The
camera comes to a complete stop and holds dead still. Blue twilight sky, anamorphic vertical
9:16, 35mm film grain.
```
Usable window: **2.6s – 3.5s** → trim to 0.90s.

BEAT NOTE (S1): the near-miss is the inciting incident — the rider's swerve away from the
foot is what shakes the key loose in S3. Frame the shoe large enough that the pull-back
reads instantly at thumbnail size.

## 5b. Recommended: 3 grouped generations instead of 7

Seedance 2.5 cuts between shots natively inside one generation, so grouping is cheaper,
holds light and wardrobe continuity better, and wastes far less of the 4s floor.
Three generations = 12s raw → trimmed to the 9.13s edit.

### GEN A — covers S1 + S2 + S3 (0.00 → 3.13)
```
Shot 1: static extreme low-angle macro on the asphalt at kerb height — a young Saudi man in
a crisp white thobe and polished black patent wedding oxfords stands at the kerb edge; his
right shoe lowers toward the road, then snaps back up onto the kerb as a red sports
motorcycle rips across the foreground left to right in heavy motion blur, kicking dust past
the lens. Cut to shot 2: extreme macro on the ground of the red motorcycle's front tire
leaned hard over, whipping past camera-left in violent horizontal blur. Cut to shot 3: tight
macro on the bike's ignition and glossy red fuel tank at speed — a brushed-steel key on a
tan leather fob jolts free, turns once with a bright specular glint and tumbles out of the
bottom of frame. Golden hour, long shadows, shallow depth of field, anamorphic vertical
9:16, natural motion blur, 35mm film grain.
```

### GEN B — covers S4 + S5 (3.13 → 5.67)
```
Shot 1: static low shot on the road along a pale concrete kerb — a brushed-steel key on a
tan leather fob drops in, bounces once off the warm asphalt, spins flat and skitters toward
the kerb, while far down the tree-lined avenue a red sports motorcycle recedes into the dusk
haze. Cut to shot 2: low ground-level shot at the top of a shallow flight of pale limestone
steps dropping into a modern villa forecourt — the key goes over the edge and tumbles down
the steps tread by tread as two grey doves startle and burst upward out of frame. The camera
pushes in slowly, staying low. Golden hour falling into blue hour, shallow depth of field,
anamorphic vertical 9:16, natural motion blur, 35mm film grain.
```

### GEN C — covers S6 + S7 (5.67 → 9.13)
```
Ground-level tracking shot across a wide travertine-paved courtyard at blue hour. A
brushed-steel key on a tan leather fob rolls across the broad joint lines of the pale stone;
the camera tracks backward at ground level staying with it as warm interior light from tall
black-framed glazing sweeps over the metal. The key slows, wobbles and settles flat on the
stone. The camera then cranes and tilts up off the paving and opens into a wide low-angle
view of a modern two-storey white villa — white cubic volumes, a tall dark-stone accent
panel on the left, black-framed floor-to-ceiling glazing glowing warm gold. A young Saudi
man in a crisp white thobe and red-and-white shemagh sits on the entrance step and looks up
toward the key. The camera comes to a complete stop and holds dead still. Blue twilight,
shallow depth of field, anamorphic vertical 9:16, 35mm film grain.
```

## 6. Single generation, first frame → last frame

Seedance 2.5 start-and-end-frame mode. Start image: S1 image. End image: S7 image.
Generate 4s, then time-stretch the edit or run it as a 8s generation and cut to 9.13s.

```
One continuous ground-level camera move, no cuts. Open in extreme close-up at road level on
the kerb edge: the white hem of a Saudi thobe over polished black wedding oxfords and long
black socks in golden light. He starts to step down off the kerb, a red sports motorcycle
bears down fast, he snaps his right foot back onto the stone and the bike rips past the
foreground and leans hard away; the ignition key tears free and falls. The camera leaves the
bike and follows the key: it hits the asphalt, spins, skitters off the kerb and tumbles down
a flight of pale limestone steps, scattering two grey doves, then rolls out across a wide
travertine courtyard as warm window light sweeps over it. The key settles flat on the stone.
The camera cranes up and back off the paving and opens into a wide low-angle view of a
modern white villa at blue hour, glazing glowing gold, a young Saudi man in a white thobe
seated on the entrance step. The light drifts from golden hour to blue hour across the move.
Anamorphic vertical 9:16, macro to wide, natural motion blur, 35mm film grain. The camera
comes to a complete stop on the final frame.
```

## 6b. Seedance 2.5 settings and continuity

- 4s minimum, 9:16, 1080p, 30fps to match the reference cadence.
- Lock the seed per generation so re-rolls keep the same paving, light and wardrobe.
- Chain the generations: export the **last frame of GEN A** and feed it as the **first frame
  of GEN B**, and the same from B into C. This is what keeps the key, the light and the
  stone consistent across the three clips.
- Motion strength / dynamism: high on GEN A (the bike), medium on GEN B, low on GEN C — the
  last generation must end dead still or the handoff frame will drift.
- If a generation invents camera shake or a zoom, add the offending word to the negative
  field rather than rewriting the prompt; Seedance obeys the negative field strongly.
- Never ask Seedance for the whole 9 seconds in one 4s job. Trim in the edit, not in the
  prompt.

## 7. The real-estate hook layer

1. **Wedding shoes + a falling key = a new home.** Never said out loud, only staged: the groom's black wedding oxfords in S1 and the key landing at his villa door in S7 close the loop by themselves.
2. **The fob turn.** As the key settles in S6, the leather fob flips over to a plain brass house-shaped tag — no text, no branding. The bike key reads as a house key one beat before the reveal.
3. **The house wakes up.** On the last frame the interior lights bloom one step brighter across the glazing — the building answers the key.
4. **The same man, both ends.** The legs in S1 and the man on the step in S7 are one person — the nine seconds are the walk to his own front door, told entirely by an object he never touched.
5. **Clean handoff plate.** S7's final frame is locked, symmetrical and empty of graphics, so the long-form villa tour cuts straight out of it on frame one.

## 8. Sound design map

| Time | Sound |
|---|---|
| 0.00–1.30 | Quiet street ambience, one leather sole scuffing the kerb, thobe rustle, a sharp intake of breath on the pull-back |
| 1.30–2.13 | Superbike scream rising, hard downshift, tire scrub, dust |
| 2.13–3.13 | Engine dopplers away, one isolated metallic key chime |
| 3.13–4.23 | Key ring on asphalt, engine fading into distance |
| 4.23–5.67 | Key pinging step to step, dove wings bursting |
| 5.67–8.23 | Key rolling on stone, low warm ambient pad rising |
| 8.23–9.13 | Everything drops out, one warm swell, evening crickets, held silence |

## 9. Production notes

- Keep the man below the knee in S1 — no face, no upper body, until the S7 reveal.
- S1 and S7 are the same person: same thobe, same black oxfords, no wardrobe drift.
- The rider's face is never visible — helmet always on, visor down.
- Keep one key design across S3–S7 (brushed steel, tan leather fob) or continuity breaks.
- Light travels golden hour → blue hour across the 9 seconds; do not reset it per shot.
- Every shot is ground-level. That is the whole grammar of the original — do not lift the camera until the S7 crane.
- No logos, no text, no watermark in any frame.
