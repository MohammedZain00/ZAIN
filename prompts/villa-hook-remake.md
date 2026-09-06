# Villa Hook — Remake Prompt Pack (9.1s / 9:16)

Source reference: 1080x1920, 30fps, 9.13s, 7 shots.
Detected cuts (s): 1.733 / 2.133 / 3.133 / 4.233 / 5.667 / 8.233

## 1. Original shot map

| # | In–Out | Dur | Content |
|---|--------|-----|---------|
| S1 | 0.00–1.73 | 1.73s | Ground-level macro: woman's legs (red polka dress + heeled sandals) walking the kerb edge, tree-lined avenue, golden hour. Vehicle enters frame right at ~1.35s |
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
| Red polka-dot short dress | Black Saudi abaya (matte crepe, flowing hem) |
| Heeled sandals | Ivory bridal heels, crystal/pearl embellishment, fine ankle strap |
| Vintage red car | Matte-black sports motorcycle (superbike), rider in black leathers + black helmet, face never seen |
| Car passes the kerb | Bike closes on the kerb near her foot, then leans hard away to avoid her |
| Lemon falls from basket | Ignition key (brushed steel + slim tan leather fob) jolts free |
| Lemon rolls across piazza | Key tumbles down a flight of stone steps into the villa forecourt |
| Pigeons | Two grey doves |
| Café table legs | Wide travertine paving, warm light spill from the villa glazing |
| Reveal: old man with cards | Reveal: the villa hero frame — Saudi man in white thobe on the entrance step |

## 3. Global style bible (prepend to every prompt)

```
Cinematic vertical 9:16, shot on ARRI Alexa with vintage anamorphic primes, T1.4,
extremely shallow depth of field, camera at ground level, warm golden-hour rolling
into blue hour, soft atmospheric haze, natural motion blur, fine 35mm grain,
palette of sand beige, travertine cream, matte black and deep charcoal,
high-end real-estate commercial look, photoreal, no stylization.
```

## 4. Negative prompt (all shots)

```
no logo, no brand mark, no watermark, no text, no captions, no subtitles, no signage,
no license plate text, no faces of the woman, no distorted hands or feet, no extra limbs,
no cartoon, no CGI plastic look, no oversaturation, no lens dirt overlay, no HDR halo,
no crowd, no cars parked in the courtyard, no daytime harsh sun
```

## 5. Shot-by-shot — image prompts + motion prompts

### S1 — 0.00 → 1.73 (1.73s)
IMAGE (first frame)
```
Ultra-low macro, camera resting on the asphalt beside a raised pale stone kerb, lens at
ankle height. A woman walks along the kerb edge — only her lower legs are in frame: the
flowing matte-black hem of a Saudi abaya swaying at mid-calf, and ivory bridal heels with
crystal and pearl embellishment and a fine ankle strap. Behind her, an upscale modern
residential street: young palms and ficus trees, blurred white cubic villas, low golden
sun raking long shadows across pale concrete. T1.4 bokeh, anamorphic vertical 9:16,
warm cinematic grade, 35mm grain.
```
MOTION
```
She takes three slow deliberate steps along the kerb edge, abaya hem swaying, heels
tapping the stone. Camera locked off on the ground, only micro parallax. At 1.3s a
matte-black sports motorcycle streaks in from the right edge, very close to the kerb,
headlight flaring, heavy motion blur. No camera shake, no zoom.
```

### S2 — 1.73 → 2.13 (0.40s)
IMAGE
```
Extreme macro at ground level: the front tire of a matte-black sports motorcycle leaned
hard over mid-corner, rubber compressed and edge-worn, warm dust and grit lifting off the
asphalt, inverted fork leg catching a low gold flare, background dissolved into creamy
bokeh of a tree-lined street.
```
MOTION
```
The bike leans further away from the kerb and whips past camera-left in 0.4 seconds,
throwing dust and heat haze into the lens. Violent horizontal motion blur, whip energy,
camera stays planted on the ground.
```

### S3 — 2.13 → 3.13 (1.00s)
IMAGE
```
Tight macro on the motorcycle's ignition barrel and glossy black fuel tank at speed. A
single brushed-steel key on a slim tan leather fob hangs from the ignition, vibrating.
The tank mirrors the smeared street; chrome bar-end and low sun flare; everything beyond
the tank is liquid bokeh.
```
MOTION
```
The bike snaps into a hard lean away from the kerb; the key jolts free of the ignition,
lifts, and tumbles out of the bottom of frame in slow motion, catching one bright
specular glint as it turns. Background rips past in horizontal motion blur.
```

### S4 — 3.13 → 4.23 (1.10s)
IMAGE
```
Ground-level shot along a pale concrete kerb line. The brushed-steel key with its tan
leather fob lies sharp in the foreground on warm asphalt; far down the tree-lined avenue
the matte-black sports motorcycle is a small receding silhouette in dusk haze, long
shadows striping the road.
```
MOTION
```
The key bounces once, spins flat on the asphalt with a metallic ring and skitters toward
the kerb edge. The motorcycle shrinks into the distance and vanishes. Camera holds low and
still; a subtle rack focus travels from the key to the departing bike and back.
```

### S5 — 4.23 → 5.67 (1.44s)
IMAGE
```
Low ground-level view at the top of a shallow flight of pale limestone steps that drop
from the pavement into a modern villa's forecourt. The brushed-steel key sits at the edge
of the top step; two grey doves stand in a warm pool of spill light on the stone; blue-hour
sky, the white cubic villa softly out of focus beyond.
```
MOTION
```
The key slides over the edge and tumbles down the steps, bouncing tread to tread with
bright metallic pings. The two doves startle and burst upward out of frame in a flutter of
wings. Camera low, slow push-in following the key down.
```

### S6 — 5.67 → 8.23 (2.56s)
IMAGE
```
Ground-level tracking macro across a vast pale travertine-paved courtyard at blue hour.
The brushed-steel key with tan leather fob rolls across the wide joint lines of the stone.
Warm interior light spills from tall black-framed floor-to-ceiling glazing onto the
paving; a modern white cubic villa looms soft and out of focus in the background.
```
MOTION
```
Camera tracks backward at ground level, staying locked with the rolling key for two
seconds; warm window light sweeps across the metal as it passes. The key slows, wobbles,
and settles flat on the stone with a final ring. The camera then begins a slow crane and
tilt upward off the paving.
```

### S7 — 8.23 → 9.13 (0.90s) — REVEAL / HANDOFF FRAME
IMAGE (this is the exact last frame = first frame of the long-form video)
```
Wide low-angle exterior of a modern two-storey white villa at dusk. Crisp white cubic
volumes, a tall dark-stone accent panel on the left elevation, black-framed floor-to-
ceiling glazing glowing warm gold, recessed downlights washing the soffits, a cantilevered
upper mass over a deep entrance recess. Pale limestone paved courtyard in the foreground
with wide joint lines, soft blue twilight sky above. A Saudi man in a white thobe and
red-and-white shemagh sits relaxed on the entrance step. Camera very low, near ground,
wide lens, clean symmetry. No text, no logo, no signage anywhere in frame.
```
MOTION
```
Camera cranes up off the paving and settles into the wide villa composition. The man on
the step looks up toward the fallen key and gives a faint smile. The interior lights bloom
one beat brighter across the glazing. Hold on the final frame, dead still.
```

## 6. Single-take first-frame → last-frame prompt

Start image: S1 image. End image: S7 image.

```
One continuous 9-second ground-level camera move, no cuts. Open at ankle height on the
kerb: a black abaya hem and ivory bridal heels walking the stone edge in golden light. A
matte-black sports motorcycle rips past the kerb and leans hard away; the ignition key
tears free and falls. The camera abandons the bike and follows the key: it hits the
asphalt, spins, skitters off the kerb and tumbles down a flight of pale limestone steps,
scattering two doves, then rolls out across a wide travertine courtyard as warm window
light sweeps over it. The key settles flat on the stone. The camera cranes up and back off
the paving and opens into a wide low-angle reveal of a modern white villa at blue hour,
glazing glowing gold, a man in a white thobe seated on the entrance step. Light drifts
from golden hour to blue hour across the move. Anamorphic, T1.4, macro to wide, natural
motion blur, 35mm grain. No text, no logo, no watermark.
```

## 7. The real-estate hook layer

1. **Bridal heels + a falling key = a new home.** Never said out loud, only staged: the wedding shoes in S1 and the key landing at the villa door in S7 close the loop by themselves.
2. **The fob turn.** As the key settles in S6, the leather fob flips over to a plain brass house-shaped tag — no text, no branding. The bike key reads as a house key one beat before the reveal.
3. **The house wakes up.** On the last frame the interior lights bloom one step brighter across the glazing — the building answers the key.
4. **Clean handoff plate.** S7's final frame is locked, symmetrical and empty of graphics, so the long-form villa tour cuts straight out of it on frame one.

## 8. Sound design map

| Time | Sound |
|---|---|
| 0.00–1.30 | Quiet street ambience, heel taps on stone, faint abaya rustle |
| 1.30–2.13 | Superbike scream rising, hard downshift, tire scrub, dust |
| 2.13–3.13 | Engine dopplers away, one isolated metallic key chime |
| 3.13–4.23 | Key ring on asphalt, engine fading into distance |
| 4.23–5.67 | Key pinging step to step, dove wings bursting |
| 5.67–8.23 | Key rolling on stone, low warm ambient pad rising |
| 8.23–9.13 | Everything drops out, one warm swell, evening crickets, held silence |

## 9. Production notes

- Keep the woman below the knee in every frame she appears in.
- The rider's face is never visible — helmet always on, visor down.
- Keep one key design across S3–S7 (brushed steel, tan leather fob) or continuity breaks.
- Light travels golden hour → blue hour across the 9 seconds; do not reset it per shot.
- Every shot is ground-level. That is the whole grammar of the original — do not lift the camera until the S7 crane.
- No logos, no text, no watermark in any frame.
