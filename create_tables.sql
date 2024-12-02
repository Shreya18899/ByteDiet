CREATE DATABASE finalproject;

USE finalproject;

CREATE TABLE image_assets (
   assetid                   INT NOT NULL AUTO_INCREMENT,
   assetname                 VARCHAR(128) NOT NULL,  -- Original name from user
   bucketkey                 VARCHAR(128) NOT NULL,  -- Random, unique name in bucket
   height                    INT NOT NULL,
   width                     INT NOT NULL,
   is_compressed             BOOLEAN NOT NULL DEFAULT FALSE,
   PRIMARY KEY (assetid),
   UNIQUE (bucketkey)
);


ALTER TABLE image_assets AUTO_INCREMENT = 1001;


---
USE finalproject;

DROP USER IF EXISTS 'photoapp-read-only';
DROP USER IF EXISTS 'photoapp-read-write';


CREATE USER 'photoapp-read-only' IDENTIFIED BY 'abc123!!';
CREATE USER 'photoapp-read-write' IDENTIFIED BY 'def456!!';


GRANT SELECT, SHOW VIEW ON photoapp.* 
      TO 'photoapp-read-only';
GRANT SELECT, SHOW VIEW, INSERT, UPDATE, DELETE, DROP, CREATE, ALTER ON finalproject.* 
      TO 'photoapp-read-write';
      
FLUSH PRIVILEGES;

