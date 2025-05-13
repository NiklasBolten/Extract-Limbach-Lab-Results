CREATE TABLE patients (
    id INTEGER,
    firstname TEXT,
    surname TEXT,
    birthday TEXT,
    gender TEXT,
    PRIMARY KEY(id)
);
CREATE TABLE parameters (
    id INTEGER,
    name TEXT,
    unit TEXT,
    reference_range TEXT,
    PRIMARY KEY(id)
);
CREATE TABLE order_number (
    id INTEGER UNIQUE, -- this is the "anr"
    patient_id INTEGER,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    PRIMARY KEY(id)
);
CREATE TABLE order_parameters (
    order_id INTEGER,
    parameter_id INTEGER,
    FOREIGN KEY (order_id) REFERENCES order_number(id),
    FOREIGN KEY (parameter_id) REFERENCES parameters(id),
    PRIMARY KEY (order_id, parameter_id)
);
