# moafqa.sa — Site Audit Handoff (update)

> Context pack for a new Claude session. Supersedes the 2026-09-22 handoff.
> Owner: Mohammed Zain, Digital Marketing Manager, Moafqa Real Estate (Riyadh).
> Last live check: **2026-09-29**. Audit history: 09-06 → 09-17 → 09-20 → 09-22 → 09-29.
> Reply to the owner in **Egyptian Arabic**, direct, no preamble.

---

## 1. Method used on 09-29 (works in the cloud container)

- Container `curl` to `moafqa.sa` **works now** (it was blocked before). Use it for raw-HTML / bot-UA checks.
- Headless Chromium via global Playwright (`/opt/node22/lib/node_modules/playwright`).
  TLS through the agent proxy: launch with
  `--ignore-certificate-errors-spki-list=<sha256 SPKI of /root/.ccr/agent-proxy-ca.crt>`
  (compute: `openssl x509 -in /root/.ccr/agent-proxy-ca.crt -pubkey -noout | openssl pkey -pubin -outform der | openssl dgst -sha256 -binary | base64`).
- Send `Accept-Language: ar-SA` or you get 303 → `/en` (see 3.3).
- Never submit the real lead form: `page.route('**/property/submit-interest-form', fulfill)`.
- To test the Lead event without polluting GA/Meta, open a property URL with
  `?conversion=property_interest&conversion_id=AUDITTEST` and abort `/g/collect` + `facebook.com/tr`.
- Meta Pixel `/tr` hits are **not observable in headless** (Meta drops automation traffic). Only `fbq()` calls can be verified.
- CARTO map API-key watermark: **out of scope** (owner request).

Deploy marker unchanged: `moafqa.css?v=20260922-english-ltr-v165` — but lots of template/JS changes shipped anyway (new pages, tracking). Don't rely on the CSS version alone.

---

## 2. Fixed since 09-22 — do NOT re-flag

| Item | Verified state |
|---|---|
| Conversion events | `view_item` + `ViewContent` on property load; `contact` + `Contact` on WhatsApp click; `generate_lead` + `Lead` (with `eventID` for CAPI dedup) after server redirect with `?conversion=property_interest&conversion_id=<id>`; `moafqa_conversion` pushed to dataLayer |
| GA4 double counting | **None.** One GA instance fires (same `gtm=` param on both `google-analytics.com` and `google.com` collect — the second is the normal Google-signals hit) |
| GTM `<noscript>` | Present |
| Footer social | Instagram / TikTok / Facebook real URLs; `sameAs` in `RealEstateAgent` schema |
| Bed/bath labels | `.mq-pd2-facts` = `المساحة 300 م² غرف النوم 4 دورات المياه 5` |
| WhatsApp prefill | Arabic, with property name + ref `PROP-2026-00060` + price (main CTA) |
| Slug collision | Fixed: `تاون-هاوس` vs `تاون-هاوس-83` (9 cards → 9 unique slugs) |
| `/projects` | Now a real projects page (`جميع المشاريع`, links to `/project/1`, CollectionPage schema) |
| Home `og:image` | `hero/1.png` (was logo) |
| New pages | `/about`, `/careers`, `/terms`, `/privacy`, `/neighborhoods`, 5× `/neighborhood/<name>`, `/project/1` — all in sitemap, all with title/desc/canonical/H1/schema |
| Sitemap | 70 URLs, 38 `lastmod`, all 200, all self-canonical |
| Listing schema | `RealEstateListing` with `offers` (price/SAR/InStock), `identifier`, `address` (locality + region), `seller`, `floorSize`, rooms |
| Image alt on galleries | `تاون هاوس للبيع في الجنادرية — 300 م² — صورة N` |
| Mobile | No horizontal scroll on 5 key pages (390px, iPhone 13 profile) |

---

## 3. Open issues — ordered by impact

### P0 — AI visibility

**3.1 Cloudflare blocks AI crawlers (403 "Your request was blocked.").**
robots.txt allows everyone, but Cloudflare's AI-bot blocking returns 403 to:
`GPTBot`, `ClaudeBot`, `CCBot`, `Bytespider`, `Amazonbot`.
Allowed (200): Googlebot, Bingbot, OAI-SearchBot, PerplexityBot, Claude-SearchBot, Applebot, DuckAssistBot, facebookexternalhit.
Fix: Cloudflare → Security → Bots / AI Crawl Control → allow at least GPTBot + ClaudeBot (or turn off "Block AI bots").

**3.2 Brand ambiguity.**
- `muwafqa.sa` is a **different WordPress site titled "موافقة العقارية"** — same Arabic name. Search engines and LLMs will mix the two.
- `mowafaqah.com` ("Moafqa Homepage | My Website") returns **410 Gone** — if it's an old Moafqa site, it should 301 to `moafqa.sa`, not 410.
- `site:moafqa.sa` on a non-Google engine returned **zero moafqa.sa pages** (only socials / Bayut / lookalikes).
- Snapchat account exists (`snapchat.com/@moafgh_10`, titled `@moafqa.sa`) but is not in `sameAs`.
Fixes: Google Business Profile, consistent NAP, FAL license on-site, add Snapchat + Bayut profile to `sameAs`, add `legalName`/`alternateName` ("Moafqa", "MOAFQA REALS", "موافقة") to schema.

**3.3 Language auto-redirect.**
Requests with no `Accept-Language` (most AI fetchers: `ChatGPT-User`, `Perplexity-User`, `Claude-User`, `meta-externalagent`, `Google-Extended`) get **303 → /en/**. `frontend_lang=en_US` cookie also forces `/` → `/en/` even with `Accept-Language: ar`. Googlebot is exempt (Odoo bot list). URL should be the only language authority; default (no header) should be Arabic.

### P1 — Trust / compliance / conversion

**3.4 No FAL (REGA brokerage) license number, no CR, no street address** anywhere on the site (home, property, contact, about, footer). FAL number is required in Saudi real-estate ads and is the #1 trust signal. Schema address has only locality + region.

**3.5 `/en` pages: `og:url` points to the Arabic URL** on every EN page (e.g. `/en/contactus` → `og:url https://moafqa.sa/contactus`).

**3.6 `www.moafqa.sa` serves 200** (canonical → apex, so not fatal) — should 301 to `https://moafqa.sa/`.

**3.7 Mobile header**: language globe icon clipped outside the header pill (left edge). Mobile hero: carousel prev-arrow overlaps the bullet "انتشار واسع بالرياض". No sticky call/WhatsApp bar on mobile property page.

**3.8 Contact form**: phone optional, email required — reverse it for Saudi leads. Email shows as `[email protected]` to non-JS crawlers (Cloudflare email obfuscation).

**3.9 Property page still lacks**: location map, `geo` coordinates, visible reference number (it's only in the WhatsApp text), financing calculator, agent card, related properties (1 link), share, favourite. Two WhatsApp links still have no `text=` (footer ones).

### P2 — SEO / content / performance

- **Thin content**: blog posts ~150–200 words ("1 دقائق قراءة" — grammar: should be "دقيقة واحدة"), about page ~67 words, 4 of 5 neighborhood pages ~40 words. No author, no `Article`/`BlogPosting` schema, blog index has **empty meta description**, EN blog titles end with `| موافقة العقارية`, blog `og:image` is a generic hero.
- **Duplicate titles**: two `تاون هاوس للبيع في الرياض - الجنادرية` (ar + en) — add area/rooms to title. Duplicate description on `/project/1` vs its unit.
- `/project/1` meta description is a single-unit text ("فيلا ... 300 م² 3 غرف") — should describe the project.
- Home H1 uses tatweel (`بوابتـــك للتـــملك`) and 3 `<span>`s without spaces → crawlers read `بوابتـــكللتـــملكالعقاري`. Add spaces / put tatweel in CSS only.
- Images without alt: home 26/38 (DOM), property ~50% (thumbnail duplicates). 16 non-lazy on home.
- **Weight**: home ≈ 5.7 MB transferred. Hero PNGs 838 KB + 920 KB + 781 KB; 5 Bahij font weights as **TTF** ~300 KB each (convert to WOFF2, drop unused weights); `og:image` 838 KB PNG (WhatsApp/Meta previews prefer JPG/WebP < 300 KB, 1200×630).
- JS error on every page: `web.assets_frontend_minimal.min.js:169` — Odoo autohide-menu expects `header#top .top_menu`; custom header lacks it.
- `.mq-project-empty` still has `mq-reveal-target` (latent opacity:0 empty state).
- Public Odoo defaults exposed: `/website/info` (module list/version), `/jobs` (possible duplicate of `/careers`), `/web/login`.
- No `llms.txt` (optional, low value).
- GA4 enhanced-measurement `form_submit` fires on every submit attempt → use `generate_lead` as the Key Event, not `form_submit`.
- No `Search` event on filters (nice-to-have).

---

## 4. Owner actions (no developer)

1. Search Console: submit `sitemap.xml`; URL-inspect home + 3 properties → Request indexing.
2. Cloudflare: allow GPTBot / ClaudeBot (3.1).
3. GA4: mark `generate_lead` as Key Event; Meta Events Manager: verify `Lead`, `ViewContent`, `Contact` in Test Events from a clean browser; AEM priority `Lead` first.
4. Google Business Profile with the same name/phone/address as the site.
5. Get the FAL number + CR to the developer (3.4).
6. Decide on `mowafaqah.com` (301 to moafqa.sa if it's ours).
7. Cookie-consent banner + privacy update (PDPL) — tracking is live now.

## 5. Performance snapshot (09-29, datacenter, desktop Chromium)

| TTFB (curl) | TTFB (browser) | DCL | Load | Transfer | Requests |
|---|---|---|---|---|---|
| 0.73 s | 815 ms | 3.0 s | 4.0 s | 5.7 MB | 53 |

Mobile (iPhone 13 profile) page loads: 2.4–3.5 s.
