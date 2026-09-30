# moafqa.sa — Search Console check (2026-09-30)

- URL Inspection `https://moafqa.sa/`: **indexed**, HTTPS OK. Crawled HTML = current version (title, description, canonical, hreflang, JSON-LD with `sameAs`, full rendered content).
- "Request indexing" returned Google's generic error ("واجهنا مشكلة في إرسال طلب الفهرسة") — Google-side/quota; retry later. Not needed for home (already current).

New issues seen in Google's crawled HTML of the homepage:
1. "قفلنا الباب" card `تاون هاوس ريف — العارض (T03)`: empty `data-embed-url`, `data-watch-url="https://www.youtube.com/"` → placeholder video card, opens nothing useful.
2. Rent card `أرض شمال الجنادرية` shows `سعر الإيجار 1,500,000` (400 m² land) — verify rent vs sale price / period (annual?).
3. Map data: project "فلل فاخرة" (المهدية) lists unit `فيلا زاوية مع شقتين حي الجنادرية` — district mismatch.
4. TikTok: footer + schema use `@moafqa.sa`, but the embedded homepage video is from `@moafgh_10` (same handle linked from muwafqa.sa). Decide the official account; add both to `sameAs` if both are ours.
5. Arabic footer: link text "About Us" in English; `.mq-footer-en` shows Arabic text instead of "Moafqa Real Estate".
6. Header is `header#top` without `.top_menu` → cause of the Odoo JS error (`web.assets_frontend_minimal.min.js:169`).

## Done by owner 09-30
- Home page: Request indexing accepted (priority crawl queue).
- **Sitemap submitted** in Search Console as `https://moafqa.sa/sitemap.xml` (Domain property needs the full URL; bare `sitemap.xml` is rejected as invalid). File verified as Googlebot: 200, valid XML, 70 URLs.
- Next check (~1 week): Indexing → Pages (indexed vs not-indexed + reasons), Sitemaps status/discovered count.
