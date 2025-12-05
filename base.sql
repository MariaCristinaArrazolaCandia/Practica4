DROP DATABASE IF EXISTS sensor_monitoring;
CREATE DATABASE sensor_monitoring
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE sensor_monitoring;
 

DROP TABLE IF EXISTS devices;
 
CREATE TABLE devices (
  id                BIGINT NOT NULL AUTO_INCREMENT,
  dev_eui           VARCHAR(64) NOT NULL,
  device_name       VARCHAR(255) DEFAULT NULL,
  application_name  VARCHAR(255) DEFAULT NULL,
  tenant_name       VARCHAR(255) DEFAULT NULL,
  device_profile_name VARCHAR(255) DEFAULT NULL,
  description       TEXT,
  address           VARCHAR(255) DEFAULT NULL,
  location_lat      DECIMAL(10,7) DEFAULT NULL,
  location_lon      DECIMAL(10,7) DEFAULT NULL,
  created_at        TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_devices_dev_eui (dev_eui)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;
 

DROP TABLE IF EXISTS measurements;
 
CREATE TABLE measurements (
  id         BIGINT NOT NULL AUTO_INCREMENT,
  dev_eui    VARCHAR(64) NOT NULL,
  time       DATETIME NOT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_meas_dev_time (dev_eui, time)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS uplinks;
 
CREATE TABLE uplinks (
  id                        BIGINT NOT NULL AUTO_INCREMENT,
  deduplication_id          VARCHAR(255) DEFAULT NULL,
  dev_eui                   VARCHAR(64) NOT NULL,
  time                      DATETIME NOT NULL,
  f_port                    INT DEFAULT NULL,
  f_cnt                     INT DEFAULT NULL,
  adr                       TINYINT(1) DEFAULT NULL,
  dr                        INT DEFAULT NULL,
  confirmed                 TINYINT(1) DEFAULT NULL,
  margin                    INT DEFAULT NULL,
  battery_level_unavailable TINYINT(1) DEFAULT NULL,
  external_power_source     TINYINT(1) DEFAULT NULL,
  battery_level             DECIMAL(5,2) DEFAULT NULL,
  raw_data                  VARCHAR(512) DEFAULT NULL,
  created_at                TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_uplinks_deduplication_id (deduplication_id),
  KEY idx_uplinks_time (time),
  KEY idx_uplinks_dev_time (dev_eui, time),
  CONSTRAINT fk_uplink_device
    FOREIGN KEY (dev_eui)
    REFERENCES devices (dev_eui)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS distance_measurements;
 
CREATE TABLE distance_measurements (
  id            BIGINT NOT NULL AUTO_INCREMENT,
  measurement_id BIGINT NOT NULL,
  distance      DECIMAL(10,2) DEFAULT NULL,
  position      VARCHAR(100) DEFAULT NULL,
  battery       DECIMAL(5,2) DEFAULT NULL,
  status        VARCHAR(100) DEFAULT NULL,
  unit          VARCHAR(20) DEFAULT 'cm',
  sensor_type   ENUM('EM310','EM500','LLDS12') DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_distance_measurements_meas (measurement_id),
  KEY idx_distance_sensor (sensor_type),
  CONSTRAINT distance_measurements_ibfk_1
    FOREIGN KEY (measurement_id)
    REFERENCES measurements (id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS sound_measurements;
 
CREATE TABLE sound_measurements (
  id             BIGINT NOT NULL AUTO_INCREMENT,
  uplink_id      BIGINT NOT NULL,
  laeq           DECIMAL(10,2) DEFAULT NULL,
  lai            DECIMAL(10,2) DEFAULT NULL,
  lai_max        DECIMAL(10,2) DEFAULT NULL,
  object_battery DECIMAL(5,2) DEFAULT NULL,
  status         VARCHAR(100) DEFAULT NULL,
  created_at     TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_sound_uplink (uplink_id),
  CONSTRAINT fk_sound_uplink
    FOREIGN KEY (uplink_id)
    REFERENCES uplinks (id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;