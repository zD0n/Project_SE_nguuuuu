CREATE DATABASE IF NOT EXISTS wiki_snake_storage
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE wiki_snake_storage;

CREATE TABLE IF NOT EXISTS snakes (
  id CHAR(36) PRIMARY KEY,
  name_en VARCHAR(120) NOT NULL,
  name_th VARCHAR(120) NULL,
  short_name VARCHAR(60) NULL,
  scientific_name VARCHAR(160) NULL,
  `group` VARCHAR(60) NULL,        -- venomous / non_venomous
  venom_type VARCHAR(60) NULL,     -- neurotoxic/hemotoxic/...
  symptoms_th TEXT NULL,
  habitat_th TEXT NULL,
  first_aid_th MEDIUMTEXT NULL,
  image_path VARCHAR(300) NULL,
  sources JSON NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_name_en (name_en),
  INDEX idx_name_th (name_th),
  INDEX idx_short_name (short_name),
  INDEX idx_group (`group`)
);