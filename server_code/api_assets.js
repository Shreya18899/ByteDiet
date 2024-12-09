//
// app.get('/assets', async (req, res) => {...});
//
// Return all the assets from the database:
//
const photoapp_db = require('./photoapp_db.js')

exports.get_assets = async (req, res) => {

  console.log("**Call to get /assets...");

  try {
    // MySQL in JS:
    //   https://expressjs.com/en/guide/database-integration.html#mysql
    //   https://github.com/mysqljs/mysql
    // SQL query to retrieve everything from assets
    let sql = "SELECT * from image_assets";
    photoapp_db.query(sql, (err, row) => {
      if (err){
        // If error send a json with error message and an empty data dict
        console.log("Error in getting assets");
        res.status(500).json({message : err.message, data : []});
      }
      else{
        // If no send a json with success message and an data
        console.log("Displaying all assets from database");
        res.json({"message": "success", "data": row});}
      });
  }//try
  catch (err) {
    console.log("**Error in /assets");
    console.log(err.message);
    
    res.status(500).json({
      "message": err.message,
      "data": []
    });
  }//catch

}//get
