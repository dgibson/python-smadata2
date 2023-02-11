# Python SMAData2 Database

This describes the database classes and table structure.

### base.py
Uses abstract base classes (Python `abc`) to define an interface (class and set of methods) that are implemented by `mock.py` and `sqllite.py`.  These deal with the physical sqllite database, or a mock database (Python ``set``) for testing purposes.

### Table: generation
Stores readings 
```sql
CREATE TABLE generation (
    inverter_serial INTEGER NOT NULL,
    timestamp       INTEGER NOT NULL,
    sample_type     INTEGER CHECK (sample_type = 0 OR 
                                   sample_type = 1 OR 
                                   sample_type = 2),
    total_yield     INTEGER,
    PRIMARY KEY (
        inverter_serial,
        timestamp,
        sample_type
    )
);
```
See base.py for further details.

```pythonstub
# Ad hoc samples, externally controlled
SAMPLE_ADHOC = 0
# Inverter recorded high(ish) frequency samples
SAMPLE_INV_FAST = 1
# Inverted recorded daily samples
SAMPLE_INV_DAILY = 2
```

### Table: pvoutput 
Stores records of uploads to PVOutput.org  
```sql
CREATE TABLE pvoutput (
    sid                    STRING,
    last_datetime_uploaded INTEGER
);
```



### Table: EventData 
Stores events as reported by the SMA device.
These include setting time, error conditions.   
```sql
CREATE TABLE EventData (
    EntryID    INT (4),
    TimeStamp  DATETIME      NOT NULL,
    Serial     INT (4)       NOT NULL,
    SusyID     INT (2),
    EventCode  INT (4),
    EventType  VARCHAR (32),
    Category   VARCHAR (32),
    EventGroup VARCHAR (32),
    Tag        VARCHAR (200),
    OldValue   VARCHAR (32),
    NewValue   VARCHAR (32),
    UserGroup  VARCHAR (10),
    PRIMARY KEY (
        Serial,
        EntryID
    )
);
```

### Table: SpotData 
Stores spot readings from the SMA device.
These include V, I for 3 phases , Grid Frequency, Temperature, BT signal.
Readings have any scale factor applied.
Some redundant fields
```sql
CREATE TABLE SpotData (
    TimeStamp     DATETIME     NOT NULL,
    Serial        INT (4)      NOT NULL,
    Pdc1          INT,
    Pdc2          INT,
    Idc1          FLOAT,
    Idc2          FLOAT,
    Udc1          FLOAT,
    Udc2          FLOAT,
    Pac1          INT,
    Pac2          INT,
    Pac3          INT,
    Iac1          FLOAT,
    Iac2          FLOAT,
    Iac3          FLOAT,
    Uac1          FLOAT,
    Uac2          FLOAT,
    Uac3          FLOAT,
    EToday        INT (8),
    ETotal        INT (8),
    Frequency     FLOAT,
    OperatingTime DOUBLE,
    FeedInTime    DOUBLE,
    BT_Signal     FLOAT,
    Status        VARCHAR (10),
    GridRelay     VARCHAR (10),
    Temperature   FLOAT,
    PRIMARY KEY (
        TimeStamp,
        Serial
    )
);

```