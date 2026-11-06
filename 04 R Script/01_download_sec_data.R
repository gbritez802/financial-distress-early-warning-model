# Create SEC folder if it does not exist
dir.create("01_raw_data/sec_financials",
           recursive = TRUE,
           showWarnings = FALSE)

# Years and quarters we want
years <- 2025
quarters <- 1:4

# Download SEC quarterly financial statement datasets
for (year in years) {
  
  for (quarter in quarters) {
    
    file_name <- paste0(year, "q", quarter, ".zip")
    
    url <- paste0(
      "https://www.sec.gov/files/dera/data/financial-statement-data-sets/",
      file_name
    )
    
    destination <- file.path(
      "01_raw_data/sec_financials",
      file_name
    )
    
    if (!file.exists(destination)) {
      
      print(paste("Downloading:", file_name))
      
      download.file(
        url,
        destination,
        mode = "wb"
      )
      
    } else {
      
      print(paste("Already downloaded:", file_name))
      
    }
  }
}
quarters <- 1:4

dir.create("01_raw_data/sec_financials",
           recursive = TRUE,
           showWarnings = FALSE)
url <- "https://www.sec.gov/files/dera/data/financial-statement-data-sets/2025q1.zip"
url
download.file(
  url,
  "01_raw_data/sec_financials/2025q1.zip",
  mode = "wb"
)
getwd()
