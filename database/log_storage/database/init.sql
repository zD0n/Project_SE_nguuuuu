USE log_database;

CREATE TABLE IF NOT EXISTS log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_mongo VARCHAR(24),
    id_snake VARCHAR(100),
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confi DECIMAL(5, 4),
    feedback TEXT
);