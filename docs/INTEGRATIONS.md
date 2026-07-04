# Integrations

Client marketing data can arrive two ways:

1. **Admin-supplied (default now):** an admin enters daily metrics and connects
   integrations from **Admin → Clients → *client***. This needs no third-party keys.
2. **Automated pulls:** drop credentials into `backend/.env` and use the integration
   clients in `backend/app/services/integrations/`. Each exposes `is_configured()` and
   `fetch_summary()` and degrades gracefully when unconfigured.

Below are the exact request shapes / env vars for each provider.

## Meta Marketing API
`services/integrations/__init__.py → MetaAdsClient`
```
META_ACCESS_TOKEN=EAAB...
# GET https://graph.facebook.com/v19.0/act_<AD_ACCOUNT_ID>/insights
#   ?fields=spend,reach,frequency,ctr,clicks,impressions,cpm,actions,purchase_roas
#   &date_preset=last_30d&access_token=<token>
```

## Shopify Admin API
`ShopifyClient`
```
SHOPIFY_STORE_DOMAIN=yourshop.myshopify.com
SHOPIFY_ADMIN_TOKEN=shpat_...
# GET https://<domain>/admin/api/2024-10/orders.json?status=any&limit=50
#   header: X-Shopify-Access-Token: <token>
```

## WooCommerce REST API
`WooCommerceClient`
```
WOOCOMMERCE_URL=https://yourstore.com
WOOCOMMERCE_KEY=ck_...
WOOCOMMERCE_SECRET=cs_...
# GET {url}/wp-json/wc/v3/orders?per_page=50   (HTTP Basic auth: key:secret)
```

## Google Analytics 4
`GA4Client` — Data API (`google-analytics-data`)
```
GOOGLE_APPLICATION_CREDENTIALS=/path/service-account.json
GA4_PROPERTY_ID=123456789
# runReport on properties/<id> with dimensions=date & metrics=sessions,activeUsers,...
```

## Google Search Console
`SearchConsoleClient` — Webmasters API (`searchanalytics.query`)
```
GOOGLE_APPLICATION_CREDENTIALS=/path/service-account.json
SEARCH_CONSOLE_SITE_URL=sc-domain:yoursite.com
# POST https://www.googleapis.com/webmasters/v3/sites/<site>/searchAnalytics/query
#   body: { startDate, endDate, dimensions:["query"], rowLimit:25 }
```

## Microsoft Clarity
Heatmaps are embedded (placeholder). Add your Clarity project via the client's
integrations panel; embed the Clarity dashboard URL or script tag on the frontend.

## Gemini AI
`services/ai.py`
```
GEMINI_API_KEY=...
# Uses model gemini-1.5-flash to turn recent metrics into insights.
# Without a key, a deterministic rule-based analyzer produces the same shape.
pip install google-generativeai   # only if you enable it
```

## Resend (email)
`services/email.py`
```
RESEND_API_KEY=re_...
[email protected]
pip install resend                # only if you enable it
```

## Supabase Storage (documents)
`services/storage.py`
```
SUPABASE_URL=https://kiupgoucjytmuxygblps.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_STORAGE_BUCKET=crux-documents
# Uploads POST to /storage/v1/object/<bucket>/<file>; without the key, files are
# written to backend/uploads/ and served at /uploads/<file>.
```
