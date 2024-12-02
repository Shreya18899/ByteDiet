//
// config.js
//
// Web service configuration parameters, separate
// from our photoapp-config file that contains 
// AWS-specific configuration information.
//

const config = {
  photoapp_config: "server_config.ini",
  photoapp_profile: "s3readwrite",
  service_port: 8081,
  page_size: 12
};

module.exports = config;
