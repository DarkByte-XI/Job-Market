-- Fonction de trigger pour job_offers
CREATE OR REPLACE FUNCTION log_job_offers_changes()
RETURNS trigger AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO job_offers_log (job_id, action, created_at)
        VALUES (NEW.job_id, 'insert_job_offers', NOW());
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO job_offers_log (job_id, action, created_at)
        VALUES (NEW.job_id, 'update_job_offers', NOW());
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO job_offers_log (job_id, action, created_at, deleted_at)
        VALUES (OLD.job_id, 'delete_job_offers', NOW(), NOW());
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Création du trigger sur job_offers
CREATE TRIGGER trg_job_offers_changes
AFTER INSERT OR UPDATE OR DELETE ON job_offers
FOR EACH ROW EXECUTE FUNCTION log_job_offers_changes();


-- Fonction de trigger générique pour les tables sources
CREATE OR REPLACE FUNCTION log_source_offers_changes()
RETURNS trigger AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO job_offers_log (job_id, action, created_at)
        VALUES (NEW.job_id, 'insert_' || TG_TABLE_NAME, NOW());
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO job_offers_log (job_id, action, created_at)
        VALUES (NEW.job_id, 'update_' || TG_TABLE_NAME, NOW());
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO job_offers_log (job_id, action, created_at, deleted_at)
        VALUES (OLD.job_id, 'delete_' || TG_TABLE_NAME, NOW(), NOW());
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


-- Trigger pour adzuna_offers
CREATE TRIGGER trg_adzuna_offers_changes
AFTER INSERT OR UPDATE OR DELETE ON adzuna_offers
FOR EACH ROW EXECUTE FUNCTION log_source_offers_changes();

-- Trigger pour france_travail_offers
CREATE TRIGGER trg_france_travail_offers_changes
AFTER INSERT OR UPDATE OR DELETE ON france_travail_offers
FOR EACH ROW EXECUTE FUNCTION log_source_offers_changes();

-- Trigger pour jsearch_offers
CREATE TRIGGER trg_jsearch_offers_changes
AFTER INSERT OR UPDATE OR DELETE ON jsearch_offers
FOR EACH ROW EXECUTE FUNCTION log_source_offers_changes();
