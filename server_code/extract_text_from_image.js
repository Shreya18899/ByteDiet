const { S3Client, GetObjectCommand, PutObjectCommand } = require('@aws-sdk/client-s3');
const Tesseract = require('tesseract.js');
const photoapp_db = require('./photoapp_db.js'); // Assuming this handles your database connection
const { photoapp_s3, s3_bucket_name, s3_region_name } = require('./photoapp_s3.js');
const uuid = require('uuid');
const stream = require('stream');
const util = require('util');


// Promisify stream.pipeline for easier async/await usage
const pipeline = util.promisify(stream.pipeline);

// Helper function to query the database
function query_database(db, sql, params) {
  return new Promise((resolve, reject) => {
    db.query(sql, params, (err, results) => {
      if (err) reject(err);
      else resolve(results);
    });
  });
}

// Helper function to convert S3 stream to buffer
async function streamToBuffer(s3Stream) {
  const chunks = [];
  for await (const chunk of s3Stream) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}

exports.fetch_and_process_image = async (req, res) => {
  console.log("**Call to fetch_and_process_image");

  try {
    const { assetid } = req.body;

    if (!assetid) {
      return res.status(400).json({ message: "Missing 'assetid' in request body." });
    }

    // Query the database to get the S3 key for the given asset id
    const query = 'SELECT bucketkey FROM image_assets WHERE assetid = ?';
    const results = await query_database(photoapp_db, query, [assetid]);

    if (results.length === 0) {
      return res.status(404).json({ message: `No image found with assetid: ${assetid}` });
    }

    const bucketkey = results[0].bucketkey;
    const bucket_folder = "textract_jobs";

    console.log(`Fetching Image from S3 with key: ${bucketkey}`);

    // S3 parameters to fetch the image
    const getObjectParams = {
      Bucket: s3_bucket_name,
      Key: bucketkey,
    };

    try {
      // Fetch the image from S3
      const command = new GetObjectCommand(getObjectParams);
      const s3Response = await photoapp_s3.send(command);

      // Convert S3 stream to buffer
      const imageBuffer = await streamToBuffer(s3Response.Body);
  
      // Extract text using Tesseract.js
      console.log("Starting OCR process...");
      const { data } = await Tesseract.recognize(imageBuffer, 'eng', {
        logger: (info) => console.log(info), 
      });
      const extractedText = data.text;
      console.log("Extracted text is : ", extractedText);

      // Generate a unique key for the extracted text file
      const imageFilename = uuid.v4();
      const textKey = `${bucket_folder}/${imageFilename}.txt`;

      // S3 parameters to upload the extracted text
      const putParams = {
        Bucket: s3_bucket_name,
        Key: textKey,
        Body: extractedText,
        ContentType: "text/plain",
        ACL: "public-read",
      };

      // Upload the text file to S3
      await photoapp_s3.send(new PutObjectCommand(putParams));
      console.log("Extracted text uploaded successfully to S3.");

      const objectUrl = `https://${s3_bucket_name}.s3.${s3_region_name}.amazonaws.com/${textKey}`;
      console.log("Extracted text URL:", objectUrl);

      // Update the database with the extracted text key
      const updateQuery = 'UPDATE textract_jobs SET s3Key = ? WHERE assetid = ?';
      await query_database(photoapp_db, updateQuery, [textKey, assetid]);
      console.log("Database updated succesfully")

      return res.json({
        message: "Image text extracted and uploaded successfully.",
        s3Key: textKey,
        s3_link: objectUrl,
      });
    } catch (s3Err) {
      console.error("Error processing Image from S3:", s3Err);
      return res.status(500).json({ message: "Failed to process Image from S3." });
    }
  } catch (err) {
    console.error("**Error in fetch_and_process_image:", err.message);
    res.status(500).json({ message: "Internal server error." });
  }
};
