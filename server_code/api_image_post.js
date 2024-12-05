const sharp = require('sharp'); // Install with npm install sharp


const photoapp_db = require('./photoapp_db.js')
const { PutObjectCommand } = require('@aws-sdk/client-s3');
const { photoapp_s3, s3_bucket_name, s3_region_name } = require('./photoapp_s3.js');

const uuid = require('uuid');

function query_database(db, sql,params)
{
  let response = new Promise((resolve, reject) => {
    try 
    {
      //
      // execute the query, and when we get the callback from
      // the database server, either resolve with the results
      // or error with the error object
      //
      db.query(sql,params, (err, results, _) => {
        if (err) {
          reject(err);
        }
        else {
          resolve(results);
        }
      });
    }
    catch (err) {
      reject(err);
    }
  });
  
  // 
  // return the PROMISE back to the caller, which will
  // eventually resolve to results or an error:
  //
  return response;
}

exports.post_image = async (req, res) => {

  console.log("**Call to post /image");

  try {

    const { assetname, data, width, height } = req.body;  // data => JS object
    const bucket_folder = "image_assets";
    const image_bytes = Buffer.from(data, 'base64');
    let objectUrl = ""; 
    // console.log(data)

    // Get image dimensions using sharp
    let imageMetadata;
    try {
      imageMetadata = await sharp(image_bytes).metadata();
      console.log("Original Image Dimensions:", imageMetadata.width, imageMetadata.height);
    } catch (err) {
      console.log("Error extracting image metadata:", err);
      return res.status(400).json({
        "message": "Invalid image data",
        "assetid": -1
      });
    }

    const parsedWidth = parseInt(width, 10);
    const parsedHeight = parseInt(height, 10);
    
    if (isNaN(parsedWidth) || isNaN(parsedHeight)) {
      return res.status(400).json({
        "message": "Height and width must be valid integers.",
        "assetid": -1
      });
    }

    // Resize image using sharp
    try {
      resizedImageBytes = await sharp(image_bytes)
        .resize(parsedWidth, parsedHeight) // Resize to specified dimensions
        .toBuffer(); // Convert the resized image back to a buffer
      console.log("Image resized successfully.");
      resizedImageMetadata = await sharp(resizedImageBytes).metadata();
      console.log("Resized Image Dimensions:", resizedImageMetadata.width, resizedImageMetadata.height);
    } catch (err) {
      console.log("Error resizing image:", err);
      return res.status(500).json({
        "message": "Failed to resize image",
        "assetid": -1,
      });
    }


    const uuidd = uuid.v4();
    const s3_key = `${bucket_folder}/${uuidd}.jpg`;
    
    const s3_params = {
      Bucket: s3_bucket_name,
      Key: s3_key,
      Body: resizedImageBytes,
      ContentType: "image/jpg",
      ACL: "public-read"
    };


    try {
      await photoapp_s3.send(new PutObjectCommand(s3_params));
      console.log("Image uploaded successfully to S3.");
      objectUrl = `https://${s3_bucket_name}.s3.${s3_region_name}.amazonaws.com/${s3_key}`;
      console.log("Object URL:", objectUrl);
    } catch (err) {
      console.log("Error uploading to S3:", err);
      return res.status(500).json({
        "message": "Failed to upload image to S3",
        "assetid": -1,
      });
    }

    let insert_sql = 'INSERT INTO image_assets (assetname, bucketkey, height, width, is_resized) VALUES (?, ?, ?, ?, ?)';
    let result = await query_database(photoapp_db, insert_sql, [assetname, s3_key, height, width, true]);

    if (result.affectedRows === 1) {
      const asset_id = result.insertId;
      return res.json({
        "message": "success",
        "assetid": asset_id,
        "objectUrl":objectUrl,
        "originalImageWidth":imageMetadata.width,
        "originalImageHeight":imageMetadata.height,
        "resizedImageWidth":resizedImageMetadata.width,
        "resizedImageHeight":resizedImageMetadata.height
      });
    } else {
      return res.status(400).json({
        "message": "unsuccessfully upload the image",
        "assetid": -1,
        })
    }



  }//try
  catch (err) {
    console.log("**Error in /image");
    console.log(err.message);
    
    res.status(500).json({
      "message": err.message,
      "assetid": -1
    });
  }//catch

}//post
