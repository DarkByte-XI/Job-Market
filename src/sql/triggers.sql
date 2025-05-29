-- Fonction de trigger pour job_offers

CREATE OR REPLACE FUNCTION log_job_offers_changes()
RETURNS trigger AS $$
    -- Cette fonction permet d'enrichir la table job_offers_log avec les
    -- opérations INSERT, UPDATE et DELETE pour obtenir la disponibilité de l'offre
    -- après chaque import en DB. Cela permet par la suite de filtrer sur les offres
    -- actives uniquement afin d'identifier celles qui sont toujours publiées.
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO job_offers_log (job_id, action, created_at)
        VALUES (NEW.job_id, 'insert_job_offers', NEW.created_at);
        RETURN NEW;

    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO job_offers_log (job_id, action, created_at, updated_at)
        VALUES (OLD.job_id, 'update_job_offers', OLD.created_at,
                NOW());
        RETURN NEW;

    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO job_offers_log (job_id, action, created_at, deleted_at)
        VALUES (OLD.job_id, 'delete_job_offers',
                OLD.created_at, NOW());
        UPDATE job_offers SET status = 'inactive' WHERE job_id = OLD.job_id;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_job_offers_changes ON job_offers;
CREATE TRIGGER trg_job_offers_changes
AFTER INSERT OR UPDATE OR DELETE ON job_offers
FOR EACH ROW EXECUTE FUNCTION log_job_offers_changes();


-- 1. Fonction de trigger générique pour les tables sources
CREATE OR REPLACE FUNCTION log_source_offers_changes()
RETURNS trigger AS $$
DECLARE
  orig_created_at TIMESTAMP;
  v_job_id        INT;
BEGIN
    -- 1) Choix explicite du job_id selon l'opération
    v_job_id := CASE
                  WHEN TG_OP = 'DELETE' THEN OLD.job_id
                  ELSE NEW.job_id
                END;

    -- 2) Récupération de created_at depuis job_offers
    SELECT created_at
      INTO orig_created_at
    FROM job_offers
    WHERE job_id = v_job_id;

    IF TG_OP = 'INSERT' THEN
        INSERT INTO job_offers_log (job_id, action, created_at)
        VALUES (v_job_id, 'insert_' || TG_TABLE_NAME, orig_created_at);
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO job_offers_log (
            job_id, action, created_at, updated_at
        ) VALUES (
            v_job_id,
            'update_' || TG_TABLE_NAME,
            orig_created_at,
            NOW()
        );
        UPDATE job_offers SET status = 'active' WHERE job_id = v_job_id;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO job_offers_log (
            job_id, action, created_at, deleted_at
        ) VALUES (
            v_job_id,
            'delete_' || TG_TABLE_NAME,
            orig_created_at,
            NOW()
        );
        UPDATE job_offers SET status = 'inactive' WHERE job_id = v_job_id;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


-- 2. (Re)création des triggers pour chaque table source
DROP TRIGGER IF EXISTS trg_adzuna_offers_changes ON adzuna_offers;
CREATE TRIGGER trg_adzuna_offers_changes
AFTER INSERT OR UPDATE OR DELETE ON adzuna_offers
FOR EACH ROW EXECUTE FUNCTION log_source_offers_changes();

DROP TRIGGER IF EXISTS trg_france_travail_offers_changes ON france_travail_offers;
CREATE TRIGGER trg_france_travail_offers_changes
AFTER INSERT OR UPDATE OR DELETE ON france_travail_offers
FOR EACH ROW EXECUTE FUNCTION log_source_offers_changes();

DROP TRIGGER IF EXISTS trg_jsearch_offers_changes ON jsearch_offers;
CREATE TRIGGER trg_jsearch_offers_changes
AFTER INSERT OR UPDATE OR DELETE ON jsearch_offers
FOR EACH ROW EXECUTE FUNCTION log_source_offers_changes();