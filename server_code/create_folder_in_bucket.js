// create_folder_in_bucket.js

const fs = require('fs');
const ini = require('ini');
const { S3Client, CreateBucketCommand } = require("@aws-sdk/client-s3");

// Read and parse the .ini file
const config = ini.parse(fs.readFileSync('./server_config.ini', 'utf-8'));

// Extract AWS credentials and region from the config
const { region, aws_access_key_id, aws_secret_access_key } = config.default;

const REGION = region || "us-east-2"; // Fallback to us-east-2 if not specified
const BUCKET_NAME = "images-to-text-unique-name"; // Ensure uniqueness

const s3Client = new S3Client({
  region: REGION,
  credentials: {
    accessKeyId: aws_access_key_id,
    secretAccessKey: aws_secret_access_key,
  },
});

async function createBucket() {
  try {
    console.log(`Creating bucket: ${BUCKET_NAME}`);
    const createBucketParams = {
      Bucket: BUCKET_NAME,
      CreateBucketConfiguration: {
        LocationConstraint: REGION, // Specify the region for the bucket
      },
    };
    const data = await s3Client.send(new CreateBucketCommand(createBucketParams));
    console.log("Bucket created successfully:", JSON.stringify(data, null, 2));
  } catch (err) {
    console.error("Error creating bucket:", err);
  }
}

createBucket();
