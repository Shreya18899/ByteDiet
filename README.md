**ByteDiet
**

We are creating an app to measure nutrients in food utilizing Amazon AWS services such as S3, RDS, Lambda functions etc.

Our project focuses on a server-side application leveraging AWS services to process and manage images and associated data efficiently. 

The server performs three key operations: 
(1) resizing and compressing images to optimize storage and bandwidth which are uploaded by the client
(2) converting images into PDFs for document management
(3) Extracting and analyzing text from images (e.g., nutritional facts) to compute relevant metrics like calorie counts and attach the image to the output. 

AWS RDS is utilized to store and manage metadata and computation results, ensuring robust and scalable database management. The system also integrates AWS Lambda for image processing and S3 for storage. By automating image handling, text extraction, and data computations, the application streamlines workflows and delivers actionable insights.

