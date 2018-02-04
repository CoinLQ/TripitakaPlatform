DROP SEQUENCE IF EXISTS task_seq;
CREATE SEQUENCE task_seq
        INCREMENT 1
        MINVALUE 1
        MAXVALUE 999999
        START 1
        CACHE 1
        CYCLE;
CREATE SEQUENCE schedule_seq
        INCREMENT 1
        MINVALUE 1
        MAXVALUE 999
        START 1
        CACHE 1
        CYCLE;

CREATE or REPLACE FUNCTION fn_schedule_seq() RETURNS trigger AS $fn_schedule_seq$
BEGIN NEW.schedule_no := 'P'||to_char(now(),'YYYYMMDD')||lpad(nextval('schedule_seq')::char, 3, '0');
RETURN NEW;
END;
$fn_schedule_seq$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS cc_schedule_seq ON rect_schedule;
CREATE TRIGGER cc_schedule_seq
    BEFORE INSERT ON rect_schedule
            FOR EACH ROW
            EXECUTE PROCEDURE fn_schedule_seq();

-- CREATE or REPLACE FUNCTION fn_gen_sid() RETURNS trigger AS $fn_gen_sid$
-- BEGIN NEW.sid := NEW.tripitaka_id||lpad(NEW.code, 5, '0')||NEW.variant_code;
-- RETURN NEW;
-- END;
-- $fn_gen_sid$ LANGUAGE plpgsql;

-- DROP TRIGGER IF EXISTS fn_gen_sid ON rect_sutra;
-- CREATE TRIGGER fn_gen_sid
--     BEFORE INSERT ON rect_sutra
--             FOR EACH ROW
--             EXECUTE PROCEDURE fn_gen_sid();

-- CREATE or REPLACE FUNCTION fn_gen_rid() RETURNS trigger AS $fn_gen_rid$
-- BEGIN NEW.rid := NEW.sutra_id||'r'|| to_char(NEW.reel_no,'FM000') ;
-- RETURN NEW;
-- END;
-- $fn_gen_rid$ LANGUAGE plpgsql;

-- DROP TRIGGER IF EXISTS fn_gen_rid ON rect_reel;
-- CREATE TRIGGER fn_gen_rid
--     BEFORE INSERT ON rect_reel
--             FOR EACH ROW
--             EXECUTE PROCEDURE fn_gen_rid();


-- CREATE or REPLACE FUNCTION fn_gen_pid() RETURNS trigger AS $fn_gen_pid$
-- BEGIN
-- IF NEW.bar_no IS NULL THEN
-- NEW.bar_no := '0';
-- END IF;
-- IF NEW.vol_no = 0 OR NEW.vol_no IS NULL THEN
-- NEW.pid := LEFT(NEW.reel_id, 8)||'r'||to_char(NEW.reel_no,'FM000')||'p'||to_char(NEW.reel_page_no,'FM00000')||NEW.bar_no;
-- ELSIF NEW.envelop_no = 0 OR NEW.envelop_no IS NULL THEN
-- NEW.pid := LEFT(NEW.reel_id, 8)||'v'||to_char(NEW.vol_no,'FM000')||'p'||to_char(NEW.page_no,'FM00000')||NEW.bar_no;
-- ELSE
-- NEW.pid := LEFT(NEW.reel_id, 8)||'e'||to_char(NEW.envelop_no,'FM000')||'v'||to_char(NEW.vol_no,'FM000')||'p'||to_char(NEW.page_no,'FM00000')||NEW.bar_no;
-- END IF;
-- RETURN NEW;
-- END;
-- $fn_gen_pid$ LANGUAGE plpgsql;

-- DROP TRIGGER IF EXISTS fn_gen_pid ON rect_page;
-- CREATE TRIGGER fn_gen_pid
--     BEFORE INSERT ON rect_page
--             FOR EACH ROW
--             EXECUTE PROCEDURE fn_gen_pid();

CREATE or REPLACE FUNCTION fn_create_reelstatis() RETURNS trigger AS $fn_create_reelstatis$
BEGIN
INSERT INTO rect_reel_task_statistical (schedule_id, reel_id,amount_of_cctasks,completed_cctasks,amount_of_absenttasks,completed_absenttasks,amount_of_pptasks,completed_pptasks,updated_at)
VALUES (NEW.schedule_id, NEW.reel_id,-1,0,-1,0,-1,0, now());
RETURN NEW;
END;
$fn_create_reelstatis$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS fn_create_reelstatis ON rect_schedule_reels;
CREATE TRIGGER fn_create_reelstatis
    BEFORE INSERT ON rect_schedule_reels
            FOR EACH ROW
            EXECUTE PROCEDURE fn_create_reelstatis();