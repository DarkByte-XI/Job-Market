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