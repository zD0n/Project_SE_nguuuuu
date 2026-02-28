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
  venomous VARCHAR(60) NULL,       -- ไม่มีพิษ / มีพิษ
  venom_type VARCHAR(255) NULL,     -- neurotoxic/hemotoxic/...
  symptoms_th TEXT NULL,
  habitat_th TEXT NULL,
  first_aid_th MEDIUMTEXT NULL,
  morphology TEXT NULL,
  image_path VARCHAR(300) NULL,
  sources JSON NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_name_en (name_en),
  INDEX idx_name_th (name_th),
  INDEX idx_short_name (short_name),
  INDEX idx_group (`group`)
);


LOAD DATA INFILE '/var/lib/mysql-files/snakes_common.csv'
INTO TABLE snakes
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(@sci, @thai, @class_id, @grp, @venomous, @risk, @venom0, @venom1, @morph, @symp, @hab, @aid0, @aid1, @aid2, @aid3)
SET 
  id = UUID(),
  scientific_name = @sci,
  name_en = @sci,
  name_th = @thai,
  `group` = @grp,
  venomous = @venomous,
  venom_type = CONCAT_WS(', ', NULLIF(@venom0, ''), NULLIF(@venom1, '')),
  morphology = @morph,
  symptoms_th = @symp,
  habitat_th = @hab,
  first_aid_th = CONCAT_WS(' ', NULLIF(@aid0, ''), NULLIF(@aid1, ''), NULLIF(@aid2, ''), NULLIF(@aid3, ''));


LOAD DATA INFILE '/var/lib/mysql-files/snakes_poison.csv'
INTO TABLE snakes
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(@sci, @thai, @class_id, @grp, @venomous, @risk, @venom0, @venom1, @morph, @symp, @hab, @aid0, @aid1, @aid2, @aid3)
SET 
  id = UUID(),
  scientific_name = @sci,
  name_en = @sci,
  name_th = @thai,
  `group` = @grp,
  venomous = @venomous,
  venom_type = CONCAT_WS(', ', NULLIF(@venom0, ''), NULLIF(@venom1, '')),
  morphology = @morph,
  symptoms_th = @symp,
  habitat_th = @hab,
  first_aid_th = CONCAT_WS(' ', NULLIF(@aid0, ''), NULLIF(@aid1, ''), NULLIF(@aid2, ''), NULLIF(@aid3, ''));



LOAD DATA INFILE '/var/lib/mysql-files/species.csv'
INTO TABLE snakes
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(@sci, @thai, @dummy1, @grp, @venomous, @risk, @venom0, @venom1, @morph, @symp, @hab, @aid0, @aid1, @aid2, @aid3)
SET 
  id = UUID(),
  scientific_name = @sci,
  name_en = @sci,
  name_th = @thai,
  `group` = @grp,
  venomous = @venomous,
  venom_type = CONCAT_WS(', ', NULLIF(@venom0, '0'), NULLIF(@venom1, '0')),
  morphology = @morph,
  symptoms_th = @symp,
  habitat_th = @hab,
  first_aid_th = CONCAT_WS(' ', NULLIF(@aid0, '0'), NULLIF(@aid1, '0'), NULLIF(@aid2, '0'), NULLIF(@aid3, '0'));


LOAD DATA INFILE '/var/lib/mysql-files/snakes_mild.csv'
INTO TABLE snakes
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(@sci, @thai, @class_id, @grp, @venomous, @risk, @venom0, @venom1, @morph, @symp, @hab, @aid0, @aid1, @aid2, @aid3)
SET 
  id = UUID(),
  scientific_name = @sci,
  name_en = @sci,
  name_th = @thai,
  `group` = @grp,
  venom_type = CONCAT_WS(', ', NULLIF(@venom0, ''), NULLIF(@venom1, '')),
  morphology = @morph,
  symptoms_th = @symp,
  habitat_th = @hab,
  first_aid_th = CONCAT_WS(' ', NULLIF(@aid0, ''), NULLIF(@aid1, ''), NULLIF(@aid2, ''), NULLIF(@aid3, ''));