const express = require('express');
const app = express();
const port = 8081; 

// Middleware to parse JSON bodies
app.use(express.json());

// Existing imports
const { GetObjectCommand, PutObjectCommand } = require("@aws-sdk/client-s3");
const { photoapp_s3, s3_bucket_name, s3_region_name } = require("./photoapp_s3.js");
const photoapp_db = require("./photoapp_db.js");
const PDFDocument = require("pdfkit");
const uuid = require("uuid");

// Helper function to query the database
function query_database(db, sql, params) {
  return new Promise((resolve, reject) => {
    db.query(sql, params, (err, results) => {
      if (err) reject(err);
      else resolve(results);
    });
  });
}
// New Endpoint to Retrieve Image Details by Asset ID
exports.get_image_assetid = async (req, res) => {
    const assetid = parseInt(req.params.assetid, 10);
    if (isNaN(assetid)) {
      return res.status(400).json({ message: 'Invalid asset ID.' });
    }
  
    try {
      const sql = 'SELECT * FROM image_assets WHERE assetid = ?';
      const results = await query_database(photoapp_db, sql, [assetid]);
  
      if (results.length === 0) {
        return res.status(404).json({ message: 'Asset not found.' });
      }
  
      const asset = results[0];
      return res.json({
        assetid: asset.assetid,
        assetname: asset.assetname,
        bucketkey: asset.bucketkey,
        original_width: asset.original_width,
        original_height: asset.original_height,
        resized_width: asset.resized_width,
        resized_height: asset.resized_height,
        is_resized: asset.is_resized,
        s3_link: `https://${s3_bucket_name}.s3.${s3_region_name}.amazonaws.com/${asset.bucketkey}`
      });
    } catch (err) {
      console.error('**Error in GET /image/:assetid:', err);
      return res.status(500).json({ message: 'Internal server error.' });
    }
  };