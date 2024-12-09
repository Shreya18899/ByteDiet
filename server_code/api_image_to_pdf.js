// Server side code to convert an image to pdf and save to s3
// Steps to Implement:

//     Client sends image data or an S3 key via a POST request.
//     The server fetches the image(s) and generates a PDF.
//     The server uploads the PDF to S3 and stores metadata in the database.
//     The server responds with the S3 link to the generated PDF.

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

// Helper to fetch an image from S3
async function fetchImageFromS3(s3Key) {
  const s3_params = { Bucket: s3_bucket_name, Key: s3Key };
  const command = new GetObjectCommand(s3_params);

  const { Body } = await photoapp_s3.send(command);
  const chunks = [];
  for await (const chunk of Body) chunks.push(chunk);
  
  return Buffer.concat(chunks); // Return the image buffer
}

// Exported function to convert images to PDF
exports.image_to_pdf = async (req, res) => {
  console.log("**Call to /image-to-pdf");

  try {
    const { images, pdfName } = req.body; // 'images' is an array of S3 keys
    const bucket_folder = "pdf_assets";
    const pdf_uuid = uuid.v4();
    const pdf_key = `${bucket_folder}/${pdf_uuid}.pdf`;
  
    console.log("Accessed pdf_assets");

    if (!images || images.length === 0) {
      return res.status(400).json({
        message: "At least one image is required to create a PDF.",
        pdfId: -1,
      });
    }

    // Create a PDF document
    const pdfDoc = new PDFDocument();
    const pdfBuffers = [];

    // Collect PDF data into a buffer
    pdfDoc.on("data", (chunk) => pdfBuffers.push(chunk));
    pdfDoc.on("end", () => console.log("PDF creation complete."));

    // Add images to the PDF
    for (const imageKey of images) {
      const imageBuffer = await fetchImageFromS3(imageKey); // Fetch image from S3
      pdfDoc.addPage().image(imageBuffer, { fit: [500, 500], align: "center", valign: "center" });
    }

    pdfDoc.end();

    // Final PDF buffer
    const pdfBuffer = Buffer.concat(pdfBuffers);

    // Upload the PDF to S3
    const s3_params = {
      Bucket: s3_bucket_name,
      Key: pdf_key,
      Body: pdfBuffer,
      ContentType: "application/pdf",
      ACL: "public-read",
    };

    await photoapp_s3.send(new PutObjectCommand(s3_params));
    console.log("PDF uploaded successfully to S3.");

    const pdfUrl = `https://${s3_bucket_name}.s3.${s3_region_name}.amazonaws.com/${pdf_key}`;

    // Save metadata to the database
    const insert_sql = "INSERT INTO pdf_assets (pdfName, pdfKey, pageCount) VALUES (?, ?, ?)";
    const result = await query_database(photoapp_db, insert_sql, [pdfName, pdf_key, images.length]);

    if (result.affectedRows === 1) {
      const pdfId = result.insertId;
      return res.json({
        message: "PDF created successfully.",
        pdfId: pdfId,
        pdfUrl: pdfUrl,
      });
    } else {
      return res.status(500).json({
        message: "Failed to save PDF metadata to database.",
        pdfId: -1,
      });
    }
  } catch (err) {
    console.error("**Error in /image-to-pdf:", err.message);
    res.status(500).json({
      message: "Internal server error",
      pdfId: -1,
    });
  }
};

// // Start server
// app.listen(port, () => console.log(`Server running on port ${port}`));
