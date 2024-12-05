//
// app.post('/image/:userid', async (req, res) => {...});
//
// Uploads an image to the bucket and updates the database,
// returning the asset id assigned to this image.
//
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
    console.log(data)
    const parsedWidth = parseInt(width, 10);
    const parsedHeight = parseInt(height, 10);
    
    if (isNaN(parsedWidth) || isNaN(parsedHeight)) {
      return res.status(400).json({
        "message": "Height and width must be valid integers.",
        "assetid": -1
      });
    }

    const image_bytes = Buffer.from(data, 'base64');
    const uuidd = uuid.v4();
    const s3_key = `${bucket_folder}/${uuidd}.jpg`;
    
    const s3_params = {
      Bucket: s3_bucket_name,
      Key: s3_key,
      Body: image_bytes,
      ContentType: "image/jpg",
      ACL: "public-read"
    };

    /* TODO
    -save the original size value, width,height
    -resize it to the input width and height
    -response with new/original size, width, and height, and s3_link 
    */

    try {
      await photoapp_s3.send(new PutObjectCommand(s3_params));
      console.log("Image uploaded successfully to S3.");
      const objectUrl = `https://${s3_bucket_name}.s3.${s3_region_name}.amazonaws.com/${s3_key}`;
      console.log("Object URL:", objectUrl);
    } catch (err) {
      console.log("Error uploading to S3:", err);
      return res.status(500).json({
        "message": "Failed to upload image to S3",
        "assetid": -1
      });
    }

    let insert_sql = 'INSERT INTO image_assets (assetname, bucketkey, height, width, is_resized) VALUES (?, ?, ?, ?, ?)';
    let result = await query_database(photoapp_db, insert_sql, [assetname, s3_key, height, width, true]);

    if (result.affectedRows === 1) {
      const asset_id = result.insertId;
      return res.json({
        "message": "success",
        "assetid": asset_id
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
