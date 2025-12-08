-- ENUM typy
CREATE TYPE reservation_status AS ENUM ('new', 'confirmed', 'cancelled');

CREATE TYPE sale_type_enum AS ENUM ('percentage', 'fixed');
CREATE TYPE sale_applies_to_enum AS ENUM ('order', 'package');

CREATE TYPE order_status_enum AS ENUM ('new', 'paid', 'cancelled');

CREATE TYPE order_item_type_enum AS ENUM ('package', 'service');

CREATE TYPE user_role_enum AS ENUM ('admin', 'staff', 'guest');

CREATE TYPE page_status_enum AS ENUM ('draft', 'published');

-- pro info boxy (koho se týká)
CREATE TYPE audience_enum AS ENUM ('guest', 'staff', 'both');

-- notifikace – typy
CREATE TYPE notification_type_enum AS ENUM ('missing_announcement', 'system', 'manual');

--------------------------------------------------
-- ZÁKLADNÍ ENTITY
--------------------------------------------------

CREATE TABLE room_type (
  id          INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name        TEXT NOT NULL UNIQUE
);

CREATE TABLE room (
  id           INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name         TEXT NOT NULL UNIQUE,
  capacity     INT NOT NULL CHECK (capacity > 0),
  description  TEXT,
  is_active    BOOLEAN NOT NULL DEFAULT true,
  room_type_id INT NOT NULL REFERENCES room_type(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE TABLE guest (
  id              INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  first_name      TEXT NOT NULL,
  last_name       TEXT NOT NULL,
  email           TEXT,
  phone           TEXT,
  address         TEXT,
  city            TEXT,
  country         TEXT,
  date_of_birth   DATE,
  document_number TEXT,
  note            TEXT
);

CREATE TABLE reservation (
  id               INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  check_in_date    DATE NOT NULL,
  check_out_date   DATE NOT NULL,
  status           reservation_status NOT NULL DEFAULT 'new',
  num_adults       INT NOT NULL CHECK (num_adults >= 1),
  num_children     INT NOT NULL DEFAULT 0 CHECK (num_children >= 0),
  note_internal    TEXT,
  note_published   TEXT,
  base_price       NUMERIC(10,2) CHECK (base_price >= 0),
  total_price      NUMERIC(10,2) CHECK (total_price >= 0),
  currency         TEXT NOT NULL DEFAULT 'EUR', -- nebo 'CZK' podle potřeby
  primary_guest_id INT NOT NULL REFERENCES guest(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  room_id          INT NOT NULL REFERENCES room(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT chk_reservation_dates
    CHECK (check_in_date < check_out_date)
);

--------------------------------------------------
-- CENÍK / RATE PLÁNY
--------------------------------------------------

CREATE TABLE rate_plan (
  id          INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name        TEXT NOT NULL UNIQUE,
  description TEXT,
  is_active   BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE price_rule (
  id               INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  rate_plan_id     INT NOT NULL REFERENCES rate_plan(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  room_type_id     INT NOT NULL REFERENCES room_type(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  valid_from       DATE NOT NULL,
  valid_to         DATE NOT NULL,
  day_of_week      INT CHECK (day_of_week BETWEEN 1 AND 7), -- 1=pondělí…7=neděle (dohodnout v aplikaci)
  min_stay_nights  INT CHECK (min_stay_nights IS NULL OR min_stay_nights > 0),
  max_stay_nights  INT CHECK (max_stay_nights IS NULL OR max_stay_nights > 0),
  price_per_night  NUMERIC(10,2) NOT NULL CHECK (price_per_night >= 0),
  currency         TEXT NOT NULL DEFAULT 'EUR',
  CONSTRAINT chk_price_rule_dates
    CHECK (valid_from <= valid_to)
);

--------------------------------------------------
-- BALÍČKY A SLUŽBY
--------------------------------------------------

CREATE TABLE package (
  id                     INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name                   TEXT NOT NULL,
  description            TEXT,
  base_nights            INT NOT NULL CHECK (base_nights > 0),
  base_adults            INT NOT NULL CHECK (base_adults >= 1),
  base_children          INT NOT NULL DEFAULT 0 CHECK (base_children >= 0),
  room_type_id           INT NOT NULL REFERENCES room_type(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  price_before_discount  NUMERIC(10,2) NOT NULL CHECK (price_before_discount >= 0),
  final_price            NUMERIC(10,2) NOT NULL CHECK (final_price >= 0),
  currency               TEXT NOT NULL DEFAULT 'EUR',
  is_external            BOOLEAN NOT NULL DEFAULT false,
  external_provider_name   TEXT,   -- např. Artamon
  external_provider_contact TEXT,  -- kontakt na externího poskytovatele
  liability_disclaimer     BOOLEAN NOT NULL DEFAULT false, -- true = penzion nenese odpovědnost
  is_active              BOOLEAN NOT NULL DEFAULT true
);

-- Co balíček obsahuje za služby (sauna, wellness, večeře…)
CREATE TABLE package_service (
  id                INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  package_id        INT NOT NULL REFERENCES package(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  service_name      TEXT NOT NULL,
  quantity          INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
  included_in_price BOOLEAN NOT NULL DEFAULT true
);

--------------------------------------------------
-- SLEVY
--------------------------------------------------

CREATE TABLE sale (
  id           INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name         TEXT NOT NULL,
  description  TEXT,
  sale_type    sale_type_enum NOT NULL, -- 'percentage' nebo 'fixed'
  sale_value   NUMERIC(10,2) NOT NULL CHECK (sale_value >= 0),
  applies_to   sale_applies_to_enum NOT NULL, -- 'order' nebo 'package'
  valid_from   DATE,
  valid_to     DATE,
  is_stackable BOOLEAN NOT NULL DEFAULT false,
  priority     INT NOT NULL DEFAULT 0,
  is_active    BOOLEAN NOT NULL DEFAULT true,
  CONSTRAINT chk_sale_dates
    CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to),
  CONSTRAINT chk_sale_percentage
    CHECK (sale_type <> 'percentage' OR sale_value <= 100)
);

-- Vazba slev na balíčky
CREATE TABLE package_sale (
  id         INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  package_id INT NOT NULL REFERENCES package(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  sale_id    INT NOT NULL REFERENCES sale(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  UNIQUE (package_id, sale_id)
);

-- Vazba slev na objednávky (když se sleva vztahuje na celou objednávku)
CREATE TABLE order_sale (
  id       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  order_id INT NOT NULL,
  sale_id  INT NOT NULL,
  CONSTRAINT fk_order_sale_order
    FOREIGN KEY (order_id) REFERENCES "order"(id)
      ON UPDATE CASCADE
      ON DELETE CASCADE,
  CONSTRAINT fk_order_sale_sale
    FOREIGN KEY (sale_id) REFERENCES sale(id)
      ON UPDATE CASCADE
      ON DELETE CASCADE,
  UNIQUE (order_id, sale_id)
);

--------------------------------------------------
-- OBJEDNÁVKY A POLOŽKY
--------------------------------------------------

CREATE TABLE "order" (
  id            INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  reservation_id INT NOT NULL REFERENCES reservation(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  status        order_status_enum NOT NULL DEFAULT 'new',
  total_price   NUMERIC(10,2) CHECK (total_price >= 0),
  currency      TEXT NOT NULL DEFAULT 'EUR',
  created_at    TIMESTAMP NOT NULL DEFAULT now(),
  note_internal TEXT
);

CREATE TABLE order_item (
  id          INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  order_id    INT NOT NULL REFERENCES "order"(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  item_type   order_item_type_enum NOT NULL, -- 'package' nebo 'service'
  package_id  INT REFERENCES package(id)
    ON UPDATE CASCADE
    ON DELETE SET NULL,
  name        TEXT NOT NULL,
  quantity    INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
  unit_price  NUMERIC(10,2) CHECK (unit_price >= 0),
  total_price NUMERIC(10,2) CHECK (total_price >= 0)
);

--------------------------------------------------
-- UŽIVATELÉ / ADMIN
--------------------------------------------------

CREATE TABLE "user" (
  id            INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email         TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role          user_role_enum NOT NULL
);

--------------------------------------------------
-- REDAKČNÍ SYSTÉM (CMS)
--------------------------------------------------

CREATE TABLE page (
  id           INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  slug         TEXT UNIQUE NOT NULL,
  title        TEXT NOT NULL,
  content_json JSONB, -- hlavní obsah stránky (bloky, sekce…)
  seo_json     JSONB, -- SEO metadata (title, description, og tags…)
  status       page_status_enum NOT NULL DEFAULT 'draft',
  published_at TIMESTAMP,
  created_at   TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE media_file (
  id        INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  file_url  TEXT NOT NULL,
  alt_text  TEXT,
  meta_json JSONB, -- např. rozměry, typ, autor
  page_id   INT REFERENCES page(id)
    ON UPDATE CASCADE
    ON DELETE SET NULL
);

CREATE TABLE iframe_embed (
  id            INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title         TEXT,
  url           TEXT NOT NULL,
  settings_json JSONB, -- např. výška, šířka, parametry
  page_id       INT REFERENCES page(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

--------------------------------------------------
-- INFO BOX (DŮLEŽITÁ HLÁŠENÍ)
--------------------------------------------------

CREATE TABLE info_box (
  id           INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title        TEXT NOT NULL,
  content_json JSONB, -- text + případně strukturovaný obsah
  starts_at    TIMESTAMP,
  ends_at      TIMESTAMP,
  priority     INT NOT NULL DEFAULT 0,
  audience     audience_enum NOT NULL, -- 'guest', 'staff', 'both'
  is_active    BOOLEAN NOT NULL DEFAULT true
);
