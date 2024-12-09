CREATE TABLE images_to_text (
    textId INT AUTO_INCREMENT PRIMARY KEY,
    imageAssetId INT NOT NULL,
    textContent TEXT,
    s3Key VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (imageAssetId) REFERENCES image_assets(assetid)
);
