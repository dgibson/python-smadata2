BEGIN TRANSACTION;
    CREATE TABLE generation (inverter_serial INTEGER,
                             timestamp INTEGER,
                             total_yield INTEGER,
			     PRIMARY KEY (inverter_serial, timestamp));

    CREATE TABLE schema (magic INTEGER, version INTEGER);
    INSERT INTO schema (magic, version) VALUES (1901284673, 0);
COMMIT;
