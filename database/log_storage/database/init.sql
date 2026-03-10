USE log_database;

CREATE TABLE IF NOT EXISTS feedback_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    id_mongo VARCHAR(24) NOT NULL,
    id_snake VARCHAR(120) NOT NULL,
    confi DECIMAL(5, 2) NOT NULL,
    feedback TEXT NULL,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);