# Astrovani v2

Mobile-first Vedic astrology website/app foundation.

## Included
- Swiss Ephemeris + sidereal Lahiri Kundli API
- D1/Rashi + D9/Navamsa + Lagna + planetary degrees/houses
- Nakshatra + Pada + retrograde flag
- Vimshottari Mahadasha / Antardasha / Pratyantardasha
- Basic yoga detection
- Ashtakoota / 36 Gun matching endpoint and UI
- Panchang astronomical core (Tithi/Paksha/Nakshatra/Yoga index)
- Astrologer marketplace UI
- User, astrologer and admin dashboards
- Chat UI + Supabase Realtime-ready schema
- Reviews, wallet, transactions and withdrawals schema
- Future voice/video call database architecture; call controls are hidden from current UI
- No AI Kundli, AI astrologer or AI prediction

## Deploy
1. Create a fresh GitHub repository.
2. Upload this project's files/folders.
3. Import the repository into Vercel.
4. In Supabase, create a fresh project and run `supabase/schema.sql`.
5. Add Supabase URL/anon key when connecting the production frontend.

## Important
The package is code-validated and designed as a deployable foundation, but production authentication, billing/payment gateway, and Supabase-connected marketplace actions require project credentials and live testing. Astrology calculations should also be independently checked against a trusted ephemeris for your required conventions.
