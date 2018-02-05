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