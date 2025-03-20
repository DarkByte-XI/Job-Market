-- Index sur les clés étrangères (Optimisation des jointures)
CREATE INDEX idx_job_offers_source ON job_offers(source_id);
CREATE INDEX idx_job_offers_company ON job_offers(company_id);
CREATE INDEX idx_job_offers_location ON job_offers(location_id);

-- Index sur external_id pour éviter les doublons et accélérer les requêtes
CREATE UNIQUE INDEX idx_job_offers_external ON job_offers(external_id, source_id);

-- Index sur created_at pour améliorer les tris et les recherches par date
CREATE INDEX idx_job_offers_created_at ON job_offers(created_at DESC);

-- Index full-text pour la recherche avancée sur les titres et descriptions
--Adzuna
CREATE INDEX idx_title_search_adzuna ON adzuna_offers USING GIN (to_tsvector('french', title));
CREATE INDEX idx_description_search_adzuna ON adzuna_offers USING GIN (to_tsvector('french', description));

--France Travail
CREATE INDEX idx_title_search_france_travail ON france_travail_offers USING GIN (to_tsvector('french', title));
CREATE INDEX idx_description_search_france_travail ON france_travail_offers USING GIN (to_tsvector('french', description));

--JSearch
CREATE INDEX idx_title_search_jsearch ON jsearch_offers USING GIN (to_tsvector('french', title));
CREATE INDEX idx_description_search_jsearch ON jsearch_offers USING GIN (to_tsvector('french', description));