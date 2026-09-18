-- ASTROVANI v2 — Supabase schema
-- Run in a fresh Supabase project. Auth users are stored in auth.users.
create extension if not exists pgcrypto;

do $$ begin create type app_role as enum ('user','astrologer','admin'); exception when duplicate_object then null; end $$;
do $$ begin create type consultation_status as enum ('requested','accepted','active','ended','rejected','cancelled'); exception when duplicate_object then null; end $$;
do $$ begin create type call_status as enum ('requested','ringing','active','ended','missed','cancelled'); exception when duplicate_object then null; end $$;

create table if not exists profiles(
 id uuid primary key references auth.users(id) on delete cascade,
 full_name text,
 avatar_url text,
 role app_role not null default 'user',
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);

create table if not exists astrologers(
 id uuid primary key references profiles(id) on delete cascade,
 display_name text not null,
 bio text,
 experience_years int not null default 0,
 specialties text[] not null default '{}',
 languages text[] not null default '{}',
 is_online boolean not null default false,
 is_verified boolean not null default false,
 chat_price_per_minute numeric(10,2) not null default 0,
 call_price_per_minute numeric(10,2) not null default 0,
 discount_percent numeric(5,2) not null default 0,
 rating numeric(3,2) not null default 0,
 total_consultations int not null default 0,
 created_at timestamptz not null default now()
);

create table if not exists kundalis(
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references profiles(id) on delete cascade,
 name text not null,
 gender text,
 dob date not null,
 birth_time time not null,
 birth_place text not null,
 latitude double precision not null,
 longitude double precision not null,
 timezone text not null default 'Asia/Kolkata',
 ayanamsa text not null default 'Lahiri',
 chart_type text not null default 'Vedic',
 lagna jsonb,
 calculation_data jsonb,
 created_at timestamptz not null default now()
);

create table if not exists conversations(
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references profiles(id) on delete cascade,
 astrologer_id uuid not null references astrologers(id) on delete cascade,
 status consultation_status not null default 'requested',
 rate_per_minute numeric(10,2) not null default 0,
 discount_percent numeric(5,2) not null default 0,
 started_at timestamptz,
 ended_at timestamptz,
 duration_seconds int not null default 0,
 amount numeric(12,2) not null default 0,
 created_at timestamptz not null default now()
);

create table if not exists messages(
 id uuid primary key default gen_random_uuid(),
 conversation_id uuid not null references conversations(id) on delete cascade,
 sender_id uuid not null references profiles(id) on delete cascade,
 body text not null,
 kundali_id uuid references kundalis(id) on delete set null,
 delivered_at timestamptz,
 read_at timestamptz,
 created_at timestamptz not null default now()
);

create table if not exists reviews(
 id uuid primary key default gen_random_uuid(),
 conversation_id uuid not null references conversations(id) on delete cascade,
 user_id uuid not null references profiles(id) on delete cascade,
 astrologer_id uuid not null references astrologers(id) on delete cascade,
 rating int not null check(rating between 1 and 5),
 review_text text,
 created_at timestamptz not null default now(),
 unique(conversation_id,user_id)
);

create table if not exists call_sessions(
 id uuid primary key default gen_random_uuid(),
 conversation_id uuid references conversations(id) on delete set null,
 caller_id uuid not null references profiles(id) on delete cascade,
 receiver_id uuid not null references profiles(id) on delete cascade,
 mode text not null check(mode in ('voice','video')),
 status call_status not null default 'requested',
 started_at timestamptz,
 ended_at timestamptz,
 duration_seconds int not null default 0,
 amount numeric(12,2) not null default 0,
 created_at timestamptz not null default now()
);

create table if not exists wallets(
 user_id uuid primary key references profiles(id) on delete cascade,
 balance numeric(14,2) not null default 0,
 updated_at timestamptz not null default now()
);
create table if not exists wallet_transactions(
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references profiles(id) on delete cascade,
 type text not null check(type in ('credit','debit','refund','commission','withdrawal')),
 amount numeric(14,2) not null,
 reference_type text,
 reference_id uuid,
 note text,
 created_at timestamptz not null default now()
);
create table if not exists withdrawals(
 id uuid primary key default gen_random_uuid(),
 astrologer_id uuid not null references astrologers(id) on delete cascade,
 amount numeric(14,2) not null,
 status text not null default 'pending' check(status in ('pending','approved','rejected','paid')),
 created_at timestamptz not null default now()
);

create or replace function public.is_admin() returns boolean language sql stable security definer set search_path=public as $$ select exists(select 1 from profiles where id=auth.uid() and role='admin'); $$;

alter table profiles enable row level security;
alter table astrologers enable row level security;
alter table kundalis enable row level security;
alter table conversations enable row level security;
alter table messages enable row level security;
alter table reviews enable row level security;
alter table call_sessions enable row level security;
alter table wallets enable row level security;
alter table wallet_transactions enable row level security;
alter table withdrawals enable row level security;

drop policy if exists profiles_select_self_or_admin on profiles;
create policy profiles_select_self_or_admin on profiles for select using (id=auth.uid() or public.is_admin());
drop policy if exists profiles_update_self_or_admin on profiles;
create policy profiles_update_self_or_admin on profiles for update using (id=auth.uid() or public.is_admin()) with check (id=auth.uid() or public.is_admin());
drop policy if exists profiles_insert_self on profiles;
create policy profiles_insert_self on profiles for insert with check (id=auth.uid());

drop policy if exists astrologers_public_select on astrologers;
create policy astrologers_public_select on astrologers for select using (true);
drop policy if exists astrologers_self_update on astrologers;
create policy astrologers_self_update on astrologers for update using (id=auth.uid() or public.is_admin()) with check (id=auth.uid() or public.is_admin());
drop policy if exists astrologers_admin_insert on astrologers;
create policy astrologers_admin_insert on astrologers for insert with check (id=auth.uid() or public.is_admin());

drop policy if exists kundalis_owner_admin on kundalis;
create policy kundalis_owner_admin on kundalis for all using (user_id=auth.uid() or public.is_admin()) with check (user_id=auth.uid() or public.is_admin());

drop policy if exists conversations_participants on conversations;
create policy conversations_participants on conversations for all using (user_id=auth.uid() or astrologer_id=auth.uid() or public.is_admin()) with check (user_id=auth.uid() or astrologer_id=auth.uid() or public.is_admin());

drop policy if exists messages_participants on messages;
create policy messages_participants on messages for all using (sender_id=auth.uid() or exists(select 1 from conversations c where c.id=conversation_id and (c.user_id=auth.uid() or c.astrologer_id=auth.uid())) or public.is_admin()) with check (sender_id=auth.uid() or exists(select 1 from conversations c where c.id=conversation_id and (c.user_id=auth.uid() or c.astrologer_id=auth.uid())) or public.is_admin());

drop policy if exists reviews_public_select on reviews;
create policy reviews_public_select on reviews for select using (true);
drop policy if exists reviews_owner_insert on reviews;
create policy reviews_owner_insert on reviews for insert with check (user_id=auth.uid());

-- Calls are intentionally backend-ready; no current UI page exposes call controls.
drop policy if exists calls_participants on call_sessions;
create policy calls_participants on call_sessions for all using (caller_id=auth.uid() or receiver_id=auth.uid() or public.is_admin()) with check (caller_id=auth.uid() or receiver_id=auth.uid() or public.is_admin());

drop policy if exists wallet_self on wallets;
create policy wallet_self on wallets for select using (user_id=auth.uid() or public.is_admin());
drop policy if exists wallet_tx_self on wallet_transactions;
create policy wallet_tx_self on wallet_transactions for select using (user_id=auth.uid() or public.is_admin());
drop policy if exists withdrawals_owner_admin on withdrawals;
create policy withdrawals_owner_admin on withdrawals for all using (astrologer_id=auth.uid() or public.is_admin()) with check (astrologer_id=auth.uid() or public.is_admin());

-- Realtime publication: safe when tables are not already members.
do $$ begin alter publication supabase_realtime add table conversations; exception when duplicate_object then null; end $$;
do $$ begin alter publication supabase_realtime add table messages; exception when duplicate_object then null; end $$;
do $$ begin alter publication supabase_realtime add table call_sessions; exception when duplicate_object then null; end $$;
