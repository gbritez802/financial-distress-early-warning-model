library(httr2)

sec_folder <- file.path(getwd(), "01_RAW_DATA", "sec_financials")

dir.create(sec_folder,
           recursive = TRUE,
           showWarnings = FALSE)

dir.exists(sec_folder)

unzip(
  "01_RAW_DATA/sec_financials/2025q1.zip",
  list = TRUE
)
unzip(
  "01_RAW_DATA/sec_financials/2025q1.zip",
  files = c("sub.txt", "num.txt"),
  exdir = "01_RAW_DATA/sec_financials/2025q1"
)
sub_data <- read.delim(
  "01_RAW_DATA/sec_financials/2025q1/sub.txt",
  sep = "\t",
  stringsAsFactors = FALSE
)

View(sub_data)
num_data <- read.delim(
  "01_RAW_DATA/sec_financials/2025q1/num.txt",
  sep = "\t",
  stringsAsFactors = FALSE
)

dim(num_data)
names(num_data)
head(num_data)
apple <- subset(
  sub_data,
  cik == 320193
)

apple[, c("adsh", "cik", "name", "form", "period", "fy", "fp", "filed")]
apple_numbers <- num_data[
  num_data$adsh %in% apple$adsh,
]

head(apple_numbers)
unique(apple_numbers$tag[
  grepl(
    "Revenue|NetIncome|Assets|Liabilities|CashAndCashEquivalents|OperatingIncome",
    apple_numbers$tag,
    ignore.case = TRUE
  )
])
core_tags <- c(
  "RevenueFromContractWithCustomerExcludingAssessedTax",
  "OperatingIncomeLoss",
  "NetIncomeLoss",
  "Assets",
  "AssetsCurrent",
  "Liabilities",
  "LiabilitiesCurrent",
  "CashAndCashEquivalentsAtCarryingValue"
)

apple_core <- apple_numbers[
  apple_numbers$tag %in% core_tags,
]

apple_core[, c("tag", "ddate", "qtrs", "uom", "value")]
apple_core_consolidated <- apple_core[
  apple_core$segments == "" | is.na(apple_core$segments),
]

apple_core_consolidated[, c(
  "tag", "ddate", "qtrs", "uom", "value"
)]
apple_q1 <- data.frame(
  cik = 320193,
  company = "APPLE INC",
  fiscal_year = 2025,
  fiscal_period = "Q1",
  revenue = 124300000000,
  operating_income = 42832000000,
  net_income = 36330000000,
  assets = 344085000000,
  current_assets = 133240000000,
  liabilities = 277327000000,
  current_liabilities = 144365000000,
  cash = 30299000000
)

apple_q1
get_metric <- function(data, tag_name, date_value, qtrs_value) {
  x <- data[
    data$tag == tag_name &
      data$ddate == date_value &
      data$qtrs == qtrs_value &
      (data$segments == "" | is.na(data$segments)),
  ]
  
  if (nrow(x) == 0) return(NA)
  
  x$value[1]
}
get_metric(
  apple_numbers,
  "RevenueFromContractWithCustomerExcludingAssessedTax",
  20241231,
  1
)
apple_auto <- data.frame(
  revenue = get_metric(apple_numbers, "RevenueFromContractWithCustomerExcludingAssessedTax", 20241231, 1),
  operating_income = get_metric(apple_numbers, "OperatingIncomeLoss", 20241231, 1),
  net_income = get_metric(apple_numbers, "NetIncomeLoss", 20241231, 1),
  assets = get_metric(apple_numbers, "Assets", 20241231, 0),
  current_assets = get_metric(apple_numbers, "AssetsCurrent", 20241231, 0),
  liabilities = get_metric(apple_numbers, "Liabilities", 20241231, 0),
  current_liabilities = get_metric(apple_numbers, "LiabilitiesCurrent", 20241231, 0),
  cash = get_metric(apple_numbers, "CashAndCashEquivalentsAtCarryingValue", 20241231, 0)
)

apple_auto
extract_company_metrics <- function(cik_value, company_name, filing_date) {
  
  company_filing <- sub_data[
    sub_data$cik == cik_value &
      sub_data$filed == filing_date,
  ]
  
  company_numbers <- num_data[
    num_data$adsh %in% company_filing$adsh,
  ]
  
  data.frame(
    cik = cik_value,
    company = company_name,
    revenue = get_metric(company_numbers, "RevenueFromContractWithCustomerExcludingAssessedTax", 20241231, 1),
    operating_income = get_metric(company_numbers, "OperatingIncomeLoss", 20241231, 1),
    net_income = get_metric(company_numbers, "NetIncomeLoss", 20241231, 1),
    assets = get_metric(company_numbers, "Assets", 20241231, 0),
    current_assets = get_metric(company_numbers, "AssetsCurrent", 20241231, 0),
    liabilities = get_metric(company_numbers, "Liabilities", 20241231, 0),
    current_liabilities = get_metric(company_numbers, "LiabilitiesCurrent", 20241231, 0),
    cash = get_metric(company_numbers, "CashAndCashEquivalentsAtCarryingValue", 20241231, 0)
  )
}
apple_test <- extract_company_metrics(
  320193,
  "APPLE INC",
  20250131
)

apple_test
microsoft <- sub_data[
  sub_data$cik == 789019,
]

microsoft[, c("adsh", "cik", "name", "form", "period", "fy", "fp", "filed")]
microsoft_test <- extract_company_metrics(
  789019,
  "MICROSOFT CORP",
  20250129
)

microsoft_test
extract_company_metrics <- function(cik_value, company_name, filing_date) {
  
  company_filing <- sub_data[
    sub_data$cik == cik_value &
      sub_data$filed == filing_date,
  ]
  
  report_date <- company_filing$period[1]
  
  company_numbers <- num_data[
    num_data$adsh %in% company_filing$adsh,
  ]
  
  data.frame(
    cik = cik_value,
    company = company_name,
    report_date = report_date,
    revenue = get_metric(company_numbers, "RevenueFromContractWithCustomerExcludingAssessedTax", report_date, 1),
    operating_income = get_metric(company_numbers, "OperatingIncomeLoss", report_date, 1),
    net_income = get_metric(company_numbers, "NetIncomeLoss", report_date, 1),
    assets = get_metric(company_numbers, "Assets", report_date, 0),
    current_assets = get_metric(company_numbers, "AssetsCurrent", report_date, 0),
    liabilities = get_metric(company_numbers, "Liabilities", report_date, 0),
    current_liabilities = get_metric(company_numbers, "LiabilitiesCurrent", report_date, 0),
    cash = get_metric(company_numbers, "CashAndCashEquivalentsAtCarryingValue", report_date, 0)
  )
}
microsoft_test <- extract_company_metrics(
  789019,
  "MICROSOFT CORP",
  20250129
)

microsoft_test
sub_data[
  sub_data$cik %in% c(1652044, 1018724, 1326801),
  c("cik", "name", "form", "period", "filed")
]
test_companies <- data.frame(
  cik = c(320193, 789019, 1652044, 1018724, 1326801),
  company = c(
    "APPLE INC",
    "MICROSOFT CORP",
    "ALPHABET INC",
    "AMAZON COM INC",
    "META PLATFORMS INC"
  ),
  filed = c(
    20250131,
    20250129,
    20250205,
    20250207,
    20250130
  )
)

test_companies
results_list <- lapply(
  1:nrow(test_companies),
  function(i) {
    extract_company_metrics(
      test_companies$cik[i],
      test_companies$company[i],
      test_companies$filed[i]
    )
  }
)

test_results <- do.call(rbind, results_list)

test_results
for (company_cik in c(1652044, 1018724, 1326801)) {
  
  company_filing <- sub_data[
    sub_data$cik == company_cik,
  ]
  
  company_numbers <- num_data[
    num_data$adsh %in% company_filing$adsh,
  ]
  
  print(unique(company_numbers$tag[
    grepl(
      "Revenue|Sales|NetIncome|OperatingIncome|Liabilities",
      company_numbers$tag,
      ignore.case = TRUE
    )
  ]))
}
extract_company_metrics <- function(cik_value, company_name, filing_date) {
  
  company_filing <- sub_data[
    sub_data$cik == cik_value &
      sub_data$filed == filing_date,
  ]
  
  report_date <- company_filing$period[1]
  form_type <- company_filing$form[1]
  
  income_qtrs <- ifelse(form_type == "10-K", 4, 1)
  
  company_numbers <- num_data[
    num_data$adsh %in% company_filing$adsh,
  ]
  
  data.frame(
    cik = cik_value,
    company = company_name,
    report_date = report_date,
    revenue = {
      revenue_value <- get_metric(
        company_numbers,
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        report_date,
        income_qtrs
      )
      
      if (is.na(revenue_value)) {
        revenue_value <- get_metric(
          company_numbers,
          "Revenues",
          report_date,
          income_qtrs
        )
      }
      
      if (is.na(revenue_value)) {
        revenue_value <- get_metric(
          company_numbers,
          "RevenuesNetOfInterestExpense",
          report_date,
          income_qtrs
        )
      }
      
      revenue_value
    },
    operating_income = get_metric(company_numbers, "OperatingIncomeLoss", report_date, income_qtrs),
    net_income = get_metric(company_numbers, "NetIncomeLoss", report_date, income_qtrs),
    assets = get_metric(company_numbers, "Assets", report_date, 0),
    current_assets = get_metric(company_numbers, "AssetsCurrent", report_date, 0),
    liabilities = get_metric(company_numbers, "Liabilities", report_date, 0),
    current_liabilities = get_metric(company_numbers, "LiabilitiesCurrent", report_date, 0),
    cash = get_metric(company_numbers, "CashAndCashEquivalentsAtCarryingValue", report_date, 0)
  )
}
results_list <- lapply(
  1:nrow(test_companies),
  function(i) {
    extract_company_metrics(
      test_companies$cik[i],
      test_companies$company[i],
      test_companies$filed[i]
    )
  }
)

test_results <- do.call(rbind, results_list)

test_results
amazon_filing <- sub_data[
  sub_data$cik == 1018724 &
    sub_data$filed == 20250207,
]

amazon_numbers <- num_data[
  num_data$adsh %in% amazon_filing$adsh,
]

unique(
  amazon_numbers$tag[
    grepl("Liabilit", amazon_numbers$tag, ignore.case = TRUE)
  ]
)
unique(
  amazon_numbers$tag[
    grepl("StockholdersEquity|Equity", amazon_numbers$tag, ignore.case = TRUE)
  ]
)
extract_company_metrics <- function(cik_value, company_name, filing_date) {
  
  company_filing <- sub_data[
    sub_data$cik == cik_value &
      sub_data$filed == filing_date,
  ]
  
  report_date <- company_filing$period[1]
  form_type <- company_filing$form[1]
  
  income_qtrs <- ifelse(form_type == "10-K", 4, 1)
  
  company_numbers <- num_data[
    num_data$adsh %in% company_filing$adsh,
  ]
  
  assets_value <- get_metric(
    company_numbers, "Assets", report_date, 0
  )
  
  liabilities_value <- get_metric(
    company_numbers, "Liabilities", report_date, 0
  )
  
  if (is.na(liabilities_value)) {
    
    equity_value <- get_metric(
      company_numbers,
      "StockholdersEquity",
      report_date,
      0
    )
    
    if (is.na(equity_value)) {
      equity_value <- get_metric(
        company_numbers,
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        report_date,
        0
      )
    }
    
    liabilities_value <- assets_value - equity_value
  }
  
  revenue_value <- get_metric(
    company_numbers,
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    report_date,
    income_qtrs
  )
  
  if (is.na(revenue_value)) {
    revenue_value <- get_metric(
      company_numbers,
      "Revenues",
      report_date,
      income_qtrs
    )
  }
  
  if (is.na(revenue_value)) {
    revenue_value <- get_metric(
      company_numbers,
      "RevenuesNetOfInterestExpense",
      report_date,
      income_qtrs
    )
  }
  
  data.frame(
    cik = cik_value,
    company = company_name,
    report_date = report_date,
    revenue = revenue_value,
    operating_income = get_metric(company_numbers, "OperatingIncomeLoss", report_date, income_qtrs),
    net_income = {
      net_income_value <- get_metric(
        company_numbers,
        "NetIncomeLoss",
        report_date,
        income_qtrs
      )
      
      if (is.na(net_income_value)) {
        net_income_value <- get_metric(
          company_numbers,
          "NetIncomeLossAvailableToCommonStockholdersBasic",
          report_date,
          income_qtrs
        )
      }
      
      net_income_value
    },
    assets = assets_value,
    current_assets = get_metric(company_numbers, "AssetsCurrent", report_date, 0),
    liabilities = liabilities_value,
    current_liabilities = get_metric(company_numbers, "LiabilitiesCurrent", report_date, 0),
    cash = get_metric(company_numbers, "CashAndCashEquivalentsAtCarryingValue", report_date, 0)
  )
}

results_list <- lapply(
  1:nrow(test_companies),
  function(i) {
    extract_company_metrics(
      test_companies$cik[i],
      test_companies$company[i],
      test_companies$filed[i]
    )
  }
)

test_results <- do.call(rbind, results_list)

test_results
write.csv(
  test_results,
  "02_clean_data/test_company_financials.csv",
  row.names = FALSE
)
starter_companies <- data.frame(
  cik = c(
    320193,   # Apple
    789019,   # Microsoft
    1652044,  # Alphabet
    1018724,  # Amazon
    1326801,  # Meta
    1045810,  # Nvidia
    21344,    # Coca-Cola
    51143,    # IBM
    63908,    # McDonald's
    354950,   # Home Depot
    4962,     # American Express
    34088,    # Exxon Mobil
    731766,   # UnitedHealth
    1800,     # Abbott
    80424,    # Procter & Gamble
    1744489,  # Disney
    1075531,  # Booking Holdings
    886982,   # Goldman Sachs
    1067983,  # Berkshire Hathaway
    320187    # Nike
  ),
  company = c(
    "APPLE INC",
    "MICROSOFT CORP",
    "ALPHABET INC",
    "AMAZON COM INC",
    "META PLATFORMS INC",
    "NVIDIA CORP",
    "COCA COLA CO",
    "INTERNATIONAL BUSINESS MACHINES CORP",
    "MCDONALDS CORP",
    "HOME DEPOT INC",
    "AMERICAN EXPRESS CO",
    "EXXON MOBIL CORP",
    "UNITEDHEALTH GROUP INC",
    "ABBOTT LABORATORIES",
    "PROCTER & GAMBLE CO",
    "WALT DISNEY CO",
    "BOOKING HOLDINGS INC",
    "GOLDMAN SACHS GROUP INC",
    "BERKSHIRE HATHAWAY INC",
    "NIKE INC"
  )
)
starter_filings <- sub_data[
  sub_data$cik %in% starter_companies$cik &
    sub_data$form %in% c("10-K", "10-Q"),
  c("cik", "name", "form", "period", "filed")
]

starter_filings
starter_companies <- merge(
  starter_companies,
  starter_filings[, c("cik", "filed")],
  by = "cik"
)

starter_companies
starter_results_list <- lapply(
  1:nrow(starter_companies),
  function(i) {
    extract_company_metrics(
      starter_companies$cik[i],
      starter_companies$company[i],
      starter_companies$filed[i]
    )
  }
)

starter_results <- do.call(rbind, starter_results_list)

starter_results
colSums(is.na(starter_results))
missing_revenue_ciks <- starter_results$cik[
  is.na(starter_results$revenue)
]

for (company_cik in missing_revenue_ciks) {
  
  company_name <- starter_results$company[
    starter_results$cik == company_cik
  ]
  
  filing <- sub_data[
    sub_data$cik == company_cik,
  ]
  
  numbers <- num_data[
    num_data$adsh %in% filing$adsh,
  ]
  
  cat("\n\n---", company_name, "---\n")
  
  print(unique(
    numbers$tag[
      grepl("Revenue|Sales", numbers$tag, ignore.case = TRUE)
    ]
  ))
}
starter_results_list <- lapply(
  1:nrow(starter_companies),
  function(i) {
    extract_company_metrics(
      starter_companies$cik[i],
      starter_companies$company[i],
      starter_companies$filed[i]
    )
  }
)

starter_results <- do.call(rbind, starter_results_list)

colSums(is.na(starter_results))
missing_liability_ciks <- starter_results$cik[
  is.na(starter_results$liabilities)
]

for (company_cik in missing_liability_ciks) {
  
  company_name <- starter_results$company[
    starter_results$cik == company_cik
  ]
  
  filing <- sub_data[
    sub_data$cik == company_cik,
  ]
  
  numbers <- num_data[
    num_data$adsh %in% filing$adsh,
  ]
  
  cat("\n\n---", company_name, "---\n")
  
  print(unique(
    numbers$tag[
      grepl("Liabilit|StockholdersEquity|Equity", numbers$tag, ignore.case = TRUE)
    ]
  ))
}
colSums(is.na(starter_results))
missing_opinc_ciks <- starter_results$cik[
  is.na(starter_results$operating_income)
]

for (company_cik in missing_opinc_ciks) {
  
  company_name <- starter_results$company[
    starter_results$cik == company_cik
  ]
  
  filing <- sub_data[
    sub_data$cik == company_cik,
  ]
  
  numbers <- num_data[
    num_data$adsh %in% filing$adsh,
  ]
  
  cat("\n\n---", company_name, "---\n")
  
  print(unique(
    numbers$tag[
      grepl("OperatingIncome|IncomeFromOperations|OperatingProfit",
            numbers$tag,
            ignore.case = TRUE)
    ]
  ))
}
starter_results[
  is.na(starter_results$net_income),
  c("cik", "company")
]
booking_filing <- sub_data[
  sub_data$cik == 1075531,
]

booking_numbers <- num_data[
  num_data$adsh %in% booking_filing$adsh,
]

unique(
  booking_numbers$tag[
    grepl("NetIncome|ProfitLoss|IncomeLoss",
          booking_numbers$tag,
          ignore.case = TRUE)
  ]
)
write.csv(
  starter_results,
  "02_clean_data/starter_company_financials.csv",
  row.names = FALSE
)
install.packages("quantmod")
library(quantmod)
getSymbols("AAPL", src = "yahoo", from = "2015-01-01", to = "2026-01-01")
head(AAPL)
ticker_map <- data.frame(
  cik = c(
    1800, 4962, 21344, 34088, 51143,
    63908, 80424, 320187, 320193, 354950,
    731766, 789019, 886982, 1018724, 1045810,
    1067983, 1075531, 1326801, 1652044, 1744489
  ),
  ticker = c(
    "ABT", "AXP", "KO", "XOM", "IBM",
    "MCD", "PG", "NKE", "AAPL", "HD",
    "UNH", "MSFT", "GS", "AMZN", "NVDA",
    "BRK-B", "BKNG", "META", "GOOGL", "DIS"
  )
)

ticker_map
stock_list <- lapply(ticker_map$ticker, function(ticker) {
  
  stock <- getSymbols(
    ticker,
    src = "yahoo",
    from = "2015-01-01",
    to = "2026-01-01",
    auto.assign = FALSE
  )
  
  data.frame(
    date = index(stock),
    ticker = ticker,
    open = as.numeric(Op(stock)),
    high = as.numeric(Hi(stock)),
    low = as.numeric(Lo(stock)),
    close = as.numeric(Cl(stock)),
    volume = as.numeric(Vo(stock)),
    adjusted = as.numeric(Ad(stock))
  )
})

stock_data <- do.call(rbind, stock_list)

head(stock_data)
unique(stock_data$ticker)
table(stock_data$ticker)
write.csv(
  stock_data,
  "02_clean_data/stock_prices_2015_2025.csv",
  row.names = FALSE
)
stock_data <- stock_data[
  order(stock_data$ticker, stock_data$date),
]

stock_data$daily_return <- ave(
  stock_data$adjusted,
  stock_data$ticker,
  FUN = function(x) c(NA, diff(x) / head(x, -1))
)

head(stock_data)
stock_data$drawdown <- ave(
  stock_data$adjusted,
  stock_data$ticker,
  FUN = function(x) {
    x / cummax(x) - 1
  }
)

head(stock_data)
stock_data$major_drawdown <- ifelse(
  stock_data$drawdown <= -0.30,
  1,
  0
)

table(stock_data$major_drawdown)
stock_data$future_min_12m <- ave(
  stock_data$adjusted,
  stock_data$ticker,
  FUN = function(x) {
    sapply(seq_along(x), function(i) {
      end <- min(i + 252, length(x))
      min(x[i:end], na.rm = TRUE)
    })
  }
)
stock_data$future_drawdown_12m <-
  stock_data$future_min_12m / stock_data$adjusted - 1

head(stock_data[, c(
  "date",
  "ticker",
  "adjusted",
  "future_min_12m",
  "future_drawdown_12m"
)])
stock_data$future_major_drawdown_12m <- ifelse(
  stock_data$future_drawdown_12m <= -0.30,
  1,
  0
)

table(stock_data$future_major_drawdown_12m)
stock_data$future_major_drawdown_12m <- ave(
  stock_data$future_drawdown_12m,
  stock_data$ticker,
  FUN = function(x) {
    result <- ifelse(x <= -0.30, 1, 0)
    
    if (length(result) >= 252) {
      result[(length(result) - 251):length(result)] <- NA
    }
    
    result
  }
)

table(stock_data$future_major_drawdown_12m, useNA = "ifany")
stock_data$volatility_30d <- ave(
  stock_data$daily_return,
  stock_data$ticker,
  FUN = function(x) {
    sapply(seq_along(x), function(i) {
      if (i < 30) {
        NA
      } else {
        sd(x[(i - 29):i], na.rm = TRUE)
      }
    })
  }
)
head(
  stock_data[
    !is.na(stock_data$volatility_30d),
    c("date", "ticker", "daily_return", "volatility_30d")
  ]
)
stock_data$momentum_6m <- ave(
  stock_data$adjusted,
  stock_data$ticker,
  FUN = function(x) {
    c(
      rep(NA, 126),
      x[127:length(x)] / x[1:(length(x) - 126)] - 1
    )
  }
)
head(
  stock_data[
    !is.na(stock_data$momentum_6m),
    c("date", "ticker", "adjusted", "momentum_6m")
  ]
)
dir.create(
  "01_RAW_DATA/sec_historical",
  recursive = TRUE,
  showWarnings = FALSE
)
companyfacts_contents <- unzip(
  "01_RAW_DATA/sec_historical/companyfacts.zip",
  list = TRUE
)

head(companyfacts_contents)
dim(companyfacts_contents)
unzip(
  "01_RAW_DATA/sec_historical/companyfacts.zip",
  files = "CIK0000320193.json",
  exdir = "01_RAW_DATA/sec_historical/apple_test"
)
apple_cf <- jsonlite::fromJSON(
  "01_RAW_DATA/sec_historical/apple_test/CIK0000320193.json"
)

names(apple_cf)
names(apple_cf$facts)
head(names(apple_cf$facts$`us-gaap`), 30)
apple_assets <- apple_cf$facts$`us-gaap`$Assets$units$USD

head(apple_assets)
tail(apple_assets)
head(apple_assets)
range(apple_assets$end)
apple_assets_clean <- apple_assets[
  apple_assets$form %in% c("10-Q", "10-K") &
    apple_assets$end >= "2015-01-01" &
    apple_assets$end <= "2025-12-31",
]

apple_assets_clean <- apple_assets_clean[
  order(apple_assets_clean$end, apple_assets_clean$filed),
]

apple_assets_clean <- apple_assets_clean[
  !duplicated(apple_assets_clean$end),
]

apple_assets_clean[, c(
  "end", "val", "fy", "fp", "form", "filed"
)]
apple_assets[
  apple_assets$end == "2015-09-26",
  c("end", "val", "accn", "fy", "fp", "form", "filed", "frame")
]
apple_assets_clean[
  apple_assets_clean$end == "2015-09-26",
]
apple_revenue <- apple_cf$facts$`us-gaap`$RevenueFromContractWithCustomerExcludingAssessedTax$units$USD

head(apple_revenue)
revenue_tags <- names(apple_cf$facts$`us-gaap`)

revenue_tags[
  grepl("Revenue|Sales", revenue_tags, ignore.case = TRUE)
]
apple_rev_old <- apple_cf$facts$`us-gaap`$SalesRevenueNet$units$USD

head(apple_rev_old)
tail(apple_rev_old)
apple_rev_older <- apple_cf$facts$`us-gaap`$Revenues$units$USD

head(apple_rev_older)
tail(apple_rev_older)
apple_rev_services <- apple_cf$facts$`us-gaap`$SalesRevenueServicesGross$units$USD

head(apple_rev_services)
tail(apple_rev_services)
apple_tags <- names(apple_cf$facts$`us-gaap`)

candidate_tags <- apple_tags[
  grepl("Revenue", apple_tags, ignore.case = TRUE) |
    grepl("^SalesRevenue", apple_tags, ignore.case = TRUE)
]

for (tag in candidate_tags) {
  
  fact <- apple_cf$facts$`us-gaap`[[tag]]
  
  if (!is.null(fact$units$USD)) {
    
    x <- fact$units$USD
    
    if (all(c("end", "val", "form", "filed") %in% names(x))) {
      
      x <- x[
        x$form %in% c("10-Q", "10-K") &
          x$end >= "2015-01-01" &
          x$end <= "2016-12-31",
      ]
      
      if (nrow(x) > 0) {
        
        cat("\n\n---", tag, "---\n")
        
        print(x[, intersect(
          c("start", "end", "val", "fy", "fp", "form", "filed"),
          names(x)
        )])
      }
    }
  }
}
clean_quarterly_metric <- function(x) {
  
  x <- x[
    x$form %in% c("10-Q", "10-K") &
      x$end >= "2015-01-01" &
      x$end <= "2025-12-31",
  ]
  
  if ("start" %in% names(x)) {
    x$start <- as.Date(x$start)
    x$end <- as.Date(x$end)
    
    x$days <- as.numeric(x$end - x$start)
    
    x <- x[
      x$days >= 70 &
        x$days <= 110,
    ]
  }
  
  x <- x[
    order(x$end, x$filed),
  ]
  
  x <- x[
    !duplicated(x$end),
  ]
  
  x
}
apple_sales_clean <- clean_quarterly_metric(apple_rev_old)

apple_sales_clean[, c(
  "start", "end", "val", "fy", "fp", "form", "filed"
)]
apple_revenue_all <- rbind(
  clean_quarterly_metric(
    apple_cf$facts$`us-gaap`$SalesRevenueNet$units$USD
  ),
  clean_quarterly_metric(
    apple_cf$facts$`us-gaap`$RevenueFromContractWithCustomerExcludingAssessedTax$units$USD
  ),
  clean_quarterly_metric(
    apple_cf$facts$`us-gaap`$Revenues$units$USD
  )
)

apple_revenue_all <- apple_revenue_all[
  order(apple_revenue_all$end, apple_revenue_all$filed),
]

apple_revenue_all <- apple_revenue_all[
  !duplicated(apple_revenue_all$end),
]

apple_revenue_all[, c(
  "start", "end", "val", "fy", "fp", "form", "filed"
)]
apple_revenue_all$end
apple_annual_revenue <- apple_cf$facts$`us-gaap`$RevenueFromContractWithCustomerExcludingAssessedTax$units$USD

apple_annual_revenue <- apple_annual_revenue[
  apple_annual_revenue$form == "10-K" &
    apple_annual_revenue$fp == "FY" &
    apple_annual_revenue$end >= "2020-01-01" &
    apple_annual_revenue$end <= "2025-12-31",
]

apple_annual_revenue <- apple_annual_revenue[
  order(apple_annual_revenue$end, apple_annual_revenue$filed),
]

apple_annual_revenue[, c(
  "start", "end", "val", "fy", "fp", "form", "filed"
)]
apple_annual_revenue$start <- as.Date(apple_annual_revenue$start)
apple_annual_revenue$end <- as.Date(apple_annual_revenue$end)

apple_annual_revenue$days <- as.numeric(
  apple_annual_revenue$end - apple_annual_revenue$start
)

apple_annual_revenue <- apple_annual_revenue[
  apple_annual_revenue$days >= 330 &
    apple_annual_revenue$days <= 380,
]

apple_annual_revenue <- apple_annual_revenue[
  order(
    apple_annual_revenue$end,
    apple_annual_revenue$filed
  ),
]

apple_annual_revenue <- apple_annual_revenue[
  !duplicated(apple_annual_revenue$end),
]

apple_annual_revenue[, c(
  "start", "end", "val",
  "fy", "form", "filed", "days"
)]
apple_q4_revenue <- data.frame()

for (i in 1:nrow(apple_annual_revenue)) {
  
  fy_end <- apple_annual_revenue$end[i]
  fy_start <- apple_annual_revenue$start[i]
  fy_revenue <- apple_annual_revenue$val[i]
  fy_filed <- apple_annual_revenue$filed[i]
  fy <- apple_annual_revenue$fy[i]
  
  # Get quarter-only observations belonging to this fiscal year
  prior_quarters <- apple_revenue_all[
    as.Date(apple_revenue_all$start) >= fy_start &
      as.Date(apple_revenue_all$end) < fy_end,
  ]
  
  # We need exactly Q1, Q2 and Q3
  if (nrow(prior_quarters) == 3) {
    
    q4_value <- fy_revenue - sum(prior_quarters$val)
    
    apple_q4_revenue <- rbind(
      apple_q4_revenue,
      data.frame(
        start = as.Date(prior_quarters$end[3]) + 1,
        end = fy_end,
        val = q4_value,
        fy = fy,
        fp = "Q4",
        form = "10-K",
        filed = fy_filed
      )
    )
  }
}

apple_q4_revenue
apple_net_income <- apple_cf$facts$`us-gaap`$NetIncomeLoss$units$USD

apple_net_income_clean <- clean_quarterly_metric(
  apple_net_income
)

apple_net_income_clean[, c(
  "start", "end", "val", "fy", "fp", "form", "filed"
)]
apple_operating_income <- apple_cf$facts$`us-gaap`$OperatingIncomeLoss$units$USD

apple_operating_income_clean <- clean_quarterly_metric(
  apple_operating_income
)

apple_operating_income_clean[, c(
  "start", "end", "val", "fy", "fp", "form", "filed"
)]
build_quarterly_flow <- function(company_cf, tag_candidates) {
  
  all_quarters <- data.frame()
  annual_values <- data.frame()
  
  for (tag in tag_candidates) {
    
    fact <- company_cf$facts$`us-gaap`[[tag]]
    
    if (is.null(fact) || is.null(fact$units$USD)) {
      next
    }
    
    x <- fact$units$USD
    
    # Quarter-only observations
    if ("start" %in% names(x)) {
      
      x$start <- as.Date(x$start)
      x$end <- as.Date(x$end)
      x$days <- as.numeric(x$end - x$start)
      
      q <- x[
        x$form %in% c("10-Q", "10-K") &
          x$end >= as.Date("2015-01-01") &
          x$end <= as.Date("2025-12-31") &
          x$days >= 70 &
          x$days <= 110,
      ]
      
      all_quarters <- rbind(all_quarters, q)
      
      # Full-year observations
      fy <- x[
        x$form == "10-K" &
          x$end >= as.Date("2015-01-01") &
          x$end <= as.Date("2025-12-31") &
          x$days >= 330 &
          x$days <= 380,
      ]
      
      annual_values <- rbind(annual_values, fy)
    }
  }
  
  # Earliest available filing for each quarter
  all_quarters <- all_quarters[
    order(all_quarters$end, all_quarters$filed),
  ]
  
  all_quarters <- all_quarters[
    !duplicated(all_quarters$end),
  ]
  
  # Earliest available full-year filing
  annual_values <- annual_values[
    order(annual_values$end, annual_values$filed),
  ]
  
  annual_values <- annual_values[
    !duplicated(annual_values$end),
  ]
  
  # Reconstruct missing Q4
  for (i in 1:nrow(annual_values)) {
    
    fy_start <- annual_values$start[i]
    fy_end <- annual_values$end[i]
    
    existing <- all_quarters[
      all_quarters$start >= fy_start &
        all_quarters$end < fy_end,
    ]
    
    if (
      nrow(existing) == 3 &&
      !(fy_end %in% all_quarters$end)
    ) {
      
      q4_value <- annual_values$val[i] - sum(existing$val)
      
      q4 <- annual_values[i, ]
      q4$start <- existing$end[3] + 1
      q4$val <- q4_value
      q4$fp <- "Q4"
      q4$days <- as.numeric(q4$end - q4$start)
      
      all_quarters <- rbind(all_quarters, q4)
    }
  }
  
  all_quarters <- all_quarters[
    order(all_quarters$end),
  ]
  
  all_quarters
}
apple_revenue_test <- build_quarterly_flow(
  apple_cf,
  c(
    "SalesRevenueNet",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues"
  )
)

apple_revenue_test[, c(
  "start", "end", "val", "fy", "fp", "form", "filed"
)]
apple_net_income_test <- build_quarterly_flow(
  apple_cf,
  c(
    "NetIncomeLoss",
    "NetIncomeLossAvailableToCommonStockholdersBasic"
  )
)

apple_net_income_test[, c(
  "start", "end", "val", "fy", "fp", "form", "filed"
)]
build_point_in_time_metric <- function(company_cf, tag_candidates) {
  
  all_values <- data.frame()
  
  for (tag in tag_candidates) {
    
    fact <- company_cf$facts$`us-gaap`[[tag]]
    
    if (is.null(fact) || is.null(fact$units$USD)) {
      next
    }
    
    x <- fact$units$USD
    
    x <- x[
      x$form %in% c("10-Q", "10-K") &
        x$end >= "2015-01-01" &
        x$end <= "2025-12-31",
    ]
    
    all_values <- rbind(all_values, x)
  }
  
  # Safely handle companies that do not report this tag
  if (nrow(all_values) == 0) {
    return(
      data.frame(
        end = as.Date(character()),
        val = numeric(),
        filed = as.Date(character())
      )
    )
  }
  
  all_values <- all_values[
    order(all_values$end, all_values$filed),
  ]
  
  all_values <- all_values[
    !duplicated(all_values$end),
  ]
  
  all_values
}
apple_liabilities_test <- build_point_in_time_metric(
  apple_cf,
  c(
    "Liabilities",
    "LiabilitiesAndStockholdersEquity"
  )
)

apple_liabilities_test[, c(
  "end", "val", "fy", "fp", "form", "filed"
)]
apple_operating_income_test <- build_quarterly_flow(
  apple_cf,
  c("OperatingIncomeLoss")
)

apple_current_assets_test <- build_point_in_time_metric(
  apple_cf,
  c("AssetsCurrent")
)

apple_current_liabilities_test <- build_point_in_time_metric(
  apple_cf,
  c("LiabilitiesCurrent")
)

apple_cash_test <- build_point_in_time_metric(
  apple_cf,
  c(
    "CashAndCashEquivalentsAtCarryingValue",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"
  )
)
cat(
  "Revenue:", nrow(apple_revenue_test), "\n",
  "Operating income:", nrow(apple_operating_income_test), "\n",
  "Net income:", nrow(apple_net_income_test), "\n",
  "Assets:", nrow(apple_assets_test), "\n",
  "Current assets:", nrow(apple_current_assets_test), "\n",
  "Liabilities:", nrow(apple_liabilities_test), "\n",
  "Current liabilities:", nrow(apple_current_liabilities_test), "\n",
  "Cash:", nrow(apple_cash_test), "\n"
)
apple_fundamentals <- data.frame(
  end = apple_revenue_test$end,
  filed = apple_revenue_test$filed,
  revenue = apple_revenue_test$val
)

apple_fundamentals$operating_income <- apple_operating_income_test$val[
  match(apple_fundamentals$end, apple_operating_income_test$end)
]

apple_fundamentals$net_income <- apple_net_income_test$val[
  match(apple_fundamentals$end, apple_net_income_test$end)
]

apple_fundamentals$assets <- apple_assets_test$val[
  match(apple_fundamentals$end, apple_assets_test$end)
]

apple_fundamentals$current_assets <- apple_current_assets_test$val[
  match(apple_fundamentals$end, apple_current_assets_test$end)
]

apple_fundamentals$liabilities <- apple_liabilities_test$val[
  match(apple_fundamentals$end, apple_liabilities_test$end)
]

apple_fundamentals$current_liabilities <- apple_current_liabilities_test$val[
  match(apple_fundamentals$end, apple_current_liabilities_test$end)
]

apple_fundamentals$cash <- apple_cash_test$val[
  match(apple_fundamentals$end, apple_cash_test$end)
]

head(apple_fundamentals)
apple_operating_income_test[
  apple_operating_income_test$end >= as.Date("2015-06-01") &
    apple_operating_income_test$end <= as.Date("2015-12-31"),
  c("start", "end", "val", "fy", "fp", "form", "filed")
]
apple_annual_operating_income <- apple_cf$facts$`us-gaap`$OperatingIncomeLoss$units$USD

apple_annual_operating_income$start <- as.Date(
  apple_annual_operating_income$start
)

apple_annual_operating_income$end <- as.Date(
  apple_annual_operating_income$end
)

apple_annual_operating_income$days <- as.numeric(
  apple_annual_operating_income$end -
    apple_annual_operating_income$start
)

apple_annual_operating_income[
  apple_annual_operating_income$form == "10-K" &
    apple_annual_operating_income$days >= 330 &
    apple_annual_operating_income$days <= 380 &
    apple_annual_operating_income$end == as.Date("2015-09-26"),
  c("start", "end", "val", "fy", "fp", "form", "filed", "days")
]
apple_2015_q4_op_income <-
  7.123e10 -
  sum(
    apple_operating_income_test$val[
      apple_operating_income_test$end >= as.Date("2014-12-01") &
        apple_operating_income_test$end < as.Date("2015-09-26")
    ]
  )

apple_2015_q4_op_income
apple_operating_income_raw <- apple_cf$facts$`us-gaap`$OperatingIncomeLoss$units$USD

apple_operating_income_raw$start <- as.Date(
  apple_operating_income_raw$start
)

apple_operating_income_raw$end <- as.Date(
  apple_operating_income_raw$end
)

apple_operating_income_raw[
  apple_operating_income_raw$end >= as.Date("2014-12-01") &
    apple_operating_income_raw$end <= as.Date("2015-03-28") &
    apple_operating_income_raw$form %in% c("10-Q", "10-K"),
  c("start", "end", "val", "fy", "fp", "form", "filed")
]
apple_fundamentals$operating_income[
  apple_fundamentals$end == as.Date("2015-09-26")
] <- 1.4623e10
colSums(is.na(apple_fundamentals))
# See the first 10 company fact files
head(company_fact_files, 10)
getwd()
list.files()
list.files("01_RAW_DATA")
list.files("01_RAW_DATA/sec_historical")
unzip(
  "01_RAW_DATA/sec_historical/companyfacts.zip",
  files = "CIK0000789019.json",
  exdir = "01_RAW_DATA/sec_historical/microsoft_test"
)
microsoft_cf <- jsonlite::fromJSON(
  "01_RAW_DATA/sec_historical/microsoft_test/CIK0000789019.json"
)

names(microsoft_cf)
microsoft_revenue_test <- build_quarterly_flow(
  microsoft_cf,
  c(
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet"
  )
)

head(
  microsoft_revenue_test[, c(
    "start", "end", "val", "fy", "fp", "form", "filed"
  )]
)
microsoft_assets_test <- build_point_in_time_metric(
  microsoft_cf,
  c("Assets")
)

head(
  microsoft_assets_test[, c(
    "end", "val", "fy", "fp", "form", "filed"
  )]
)
build_company_fundamentals <- function(company_cf) {
  
  # FLOW METRICS
  
  revenue <- build_quarterly_flow(
    company_cf,
    c(
      "RevenueFromContractWithCustomerExcludingAssessedTax",
      "Revenues",
      "SalesRevenueNet"
    )
  )
  
  operating_income <- build_quarterly_flow(
    company_cf,
    c("OperatingIncomeLoss")
  )
  
  net_income <- build_quarterly_flow(
    company_cf,
    c(
      "NetIncomeLoss",
      "ProfitLoss"
    )
  )
  
  
  # POINT-IN-TIME METRICS
  
  assets <- build_point_in_time_metric(
    company_cf,
    c("Assets")
  )
  
  current_assets <- build_point_in_time_metric(
    company_cf,
    c("AssetsCurrent")
  )
  
  liabilities <- build_point_in_time_metric(
    company_cf,
    c("Liabilities")
  )
  
  if (nrow(liabilities) == 0) {
    
    equity <- build_point_in_time_metric(
      company_cf,
      c(
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"
      )
    )
    
    liabilities <- merge(
      assets[, c("end", "filed", "val")],
      equity[, c("end", "val")],
      by = "end",
      all.x = TRUE,
      suffixes = c("_assets", "_equity")
    )
    
    liabilities$val <-
      liabilities$val_assets - liabilities$val_equity
    
    liabilities <- liabilities[, c("end", "filed", "val")]
  }
  
  current_liabilities <- build_point_in_time_metric(
    company_cf,
    c("LiabilitiesCurrent")
  )
  
  cash <- build_point_in_time_metric(
    company_cf,
    c(
      "CashAndCashEquivalentsAtCarryingValue",
      "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"
    )
  )
  
  
  # STANDARDIZE COLUMNS
  
  revenue <- revenue[, c("end", "filed", "val")]
  names(revenue)[3] <- "revenue"
  
  operating_income <- operating_income[, c("end", "val")]
  names(operating_income)[2] <- "operating_income"
  
  net_income <- net_income[, c("end", "val")]
  names(net_income)[2] <- "net_income"
  
  assets <- assets[, c("end", "val")]
  names(assets)[2] <- "assets"
  
  current_assets <- current_assets[, c("end", "val")]
  names(current_assets)[2] <- "current_assets"
  
  liabilities <- liabilities[, c("end", "val")]
  names(liabilities)[2] <- "liabilities"
  
  current_liabilities <- current_liabilities[, c("end", "val")]
  names(current_liabilities)[2] <- "current_liabilities"
  
  cash <- cash[, c("end", "val")]
  names(cash)[2] <- "cash"
  
  
  # MERGE EVERYTHING
  
  fundamentals <- Reduce(
    function(x, y) merge(x, y, by = "end", all.x = TRUE),
    list(
      revenue,
      operating_income,
      net_income,
      assets,
      current_assets,
      liabilities,
      current_liabilities,
      cash
    )
  )
  
  fundamentals <- fundamentals[
    order(fundamentals$end),
  ]
  
  rownames(fundamentals) <- NULL
  
  fundamentals
}
abbott_cf <- jsonlite::fromJSON(
  "01_RAW_DATA/sec_historical/starter_20/CIK0000001800.json"
)

names(abbott_cf$facts$`us-gaap`)[
  grepl(
    "Liabilities$|StockholdersEquity",
    names(abbott_cf$facts$`us-gaap`)
  )
]
abbott_fundamentals <- build_company_fundamentals(
  abbott_cf
)

dim(abbott_fundamentals)

colSums(is.na(abbott_fundamentals))

for (i in 1:nrow(starter_companies)) {
  
  cat("Testing:", starter_companies$company[i], "\n")
  
  cf <- jsonlite::fromJSON(
    file.path(
      "01_RAW_DATA/sec_historical/starter_20",
      starter_companies$json_file[i]
    )
  )
  
  result <- try(
    build_company_fundamentals(cf),
    silent = TRUE
  )
  
  if (inherits(result, "try-error")) {
    cat("FAILED:", starter_companies$company[i], "\n")
    break
  } else {
    cat("PASSED\n")
  }
}
exxon_cf <- jsonlite::fromJSON(
  "01_RAW_DATA/sec_historical/starter_20/CIK0000034088.json"
)

exxon_tags <- names(exxon_cf$facts$`us-gaap`)

exxon_tags[
  grepl("Revenue|Sales|OperatingIncome|NetIncome|ProfitLoss",
        exxon_tags,
        ignore.case = TRUE)
]
exxon_tags[
  grepl("Operating|IncomeFromOperations|Earnings",
        exxon_tags,
        ignore.case = TRUE)
]
build_quarterly_flow <- function(company_cf, tag_candidates) {
  
  all_quarters <- data.frame()
  annual_values <- data.frame()
  
  for (tag in tag_candidates) {
    
    fact <- company_cf$facts$`us-gaap`[[tag]]
    
    if (is.null(fact) || is.null(fact$units$USD)) {
      next
    }
    
    x <- fact$units$USD
    
    if (!"start" %in% names(x)) {
      next
    }
    
    x$start <- as.Date(x$start)
    x$end <- as.Date(x$end)
    x$days <- as.numeric(x$end - x$start)
    
    q <- x[
      x$form %in% c("10-Q", "10-K") &
        x$end >= as.Date("2015-01-01") &
        x$end <= as.Date("2025-12-31") &
        x$days >= 70 &
        x$days <= 110,
    ]
    
    all_quarters <- rbind(all_quarters, q)
    
    fy <- x[
      x$form == "10-K" &
        x$end >= as.Date("2015-01-01") &
        x$end <= as.Date("2025-12-31") &
        x$days >= 330 &
        x$days <= 380,
    ]
    
    annual_values <- rbind(annual_values, fy)
  }
  
  # If nothing exists for this metric, return empty safely
  if (nrow(all_quarters) == 0) {
    return(
      data.frame(
        end = as.Date(character()),
        filed = as.Date(character()),
        val = numeric()
      )
    )
  }
  
  all_quarters <- all_quarters[
    order(all_quarters$end, all_quarters$filed),
  ]
  
  all_quarters <- all_quarters[
    !duplicated(all_quarters$end),
  ]
  
  if (nrow(annual_values) > 0) {
    
    annual_values <- annual_values[
      order(annual_values$end, annual_values$filed),
    ]
    
    annual_values <- annual_values[
      !duplicated(annual_values$end),
    ]
    
    for (i in 1:nrow(annual_values)) {
      
      fy_start <- annual_values$start[i]
      fy_end <- annual_values$end[i]
      
      existing <- all_quarters[
        all_quarters$start >= fy_start &
          all_quarters$end < fy_end,
      ]
      
      if (
        nrow(existing) == 3 &&
        !(fy_end %in% all_quarters$end)
      ) {
        
        q4_value <- annual_values$val[i] - sum(existing$val)
        
        q4 <- annual_values[i, ]
        q4$start <- existing$end[3] + 1
        q4$val <- q4_value
        q4$fp <- "Q4"
        q4$days <- as.numeric(q4$end - q4$start)
        
        all_quarters <- rbind(all_quarters, q4)
      }
    }
  }
  
  all_quarters <- all_quarters[
    order(all_quarters$end),
  ]
  
  all_quarters
}
build_company_fundamentals <- function(company_cf) {
  
  revenue <- build_quarterly_flow(
    company_cf,
    c(
      "RevenueFromContractWithCustomerExcludingAssessedTax",
      "Revenues",
      "SalesRevenueNet"
    )
  )
  
  operating_income <- build_quarterly_flow(
    company_cf,
    c("OperatingIncomeLoss")
  )
  
  net_income <- build_quarterly_flow(
    company_cf,
    c(
      "NetIncomeLoss",
      "ProfitLoss"
    )
  )
  
  assets <- build_point_in_time_metric(
    company_cf,
    c("Assets")
  )
  
  current_assets <- build_point_in_time_metric(
    company_cf,
    c("AssetsCurrent")
  )
  
  liabilities <- build_point_in_time_metric(
    company_cf,
    c("Liabilities")
  )
  
  if (nrow(liabilities) == 0) {
    
    equity <- build_point_in_time_metric(
      company_cf,
      c(
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"
      )
    )
    
    liabilities <- merge(
      assets[, c("end", "filed", "val")],
      equity[, c("end", "val")],
      by = "end",
      all.x = TRUE,
      suffixes = c("_assets", "_equity")
    )
    
    liabilities$val <-
      liabilities$val_assets - liabilities$val_equity
    
    liabilities <- liabilities[, c("end", "filed", "val")]
  }
  
  current_liabilities <- build_point_in_time_metric(
    company_cf,
    c("LiabilitiesCurrent")
  )
  
  cash <- build_point_in_time_metric(
    company_cf,
    c(
      "CashAndCashEquivalentsAtCarryingValue",
      "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"
    )
  )
  
  # Use revenue as the base quarterly calendar
  fundamentals <- revenue[, c("end", "filed", "val")]
  names(fundamentals)[3] <- "revenue"
  
  add_metric <- function(base, metric, metric_name) {
    
    if (nrow(metric) == 0) {
      base[[metric_name]] <- NA_real_
      return(base)
    }
    
    temp <- metric[, c("end", "val")]
    names(temp)[2] <- metric_name
    
    merge(base, temp, by = "end", all.x = TRUE)
  }
  
  fundamentals <- add_metric(
    fundamentals,
    operating_income,
    "operating_income"
  )
  
  fundamentals <- add_metric(
    fundamentals,
    net_income,
    "net_income"
  )
  
  fundamentals <- add_metric(
    fundamentals,
    assets,
    "assets"
  )
  
  fundamentals <- add_metric(
    fundamentals,
    current_assets,
    "current_assets"
  )
  
  fundamentals <- add_metric(
    fundamentals,
    liabilities,
    "liabilities"
  )
  
  fundamentals <- add_metric(
    fundamentals,
    current_liabilities,
    "current_liabilities"
  )
  
  fundamentals <- add_metric(
    fundamentals,
    cash,
    "cash"
  )
  
  fundamentals <- fundamentals[
    order(fundamentals$end),
  ]
  
  rownames(fundamentals) <- NULL
  
  fundamentals
}
exxon_fundamentals <- build_company_fundamentals(
  exxon_cf
)

dim(exxon_fundamentals)

colSums(is.na(exxon_fundamentals))
for (i in 1:nrow(starter_companies)) {
  
  cat("Testing:", starter_companies$company[i], "\n")
  
  cf <- jsonlite::fromJSON(
    file.path(
      "01_RAW_DATA/sec_historical/starter_20",
      starter_companies$json_file[i]
    )
  )
  
  result <- try(
    build_company_fundamentals(cf),
    silent = TRUE
  )
  
  if (inherits(result, "try-error")) {
    cat("FAILED:", starter_companies$company[i], "\n")
    break
  } else {
    cat("PASSED\n")
  }
}
reporting_exceptions <- data.frame(
  company = c(
    "AMAZON COM INC",
    "EXXON MOBIL CORP",
    "APPLE INC",
    "BOOKING HOLDINGS INC"
  ),
  issue = c(
    "No direct Liabilities tag",
    "No clean comparable OperatingIncomeLoss tag",
    "Historical revenue tags change over time; some Q4 flow values reconstructed",
    "Net income reported under NetIncomeLossAvailableToCommonStockholdersBasic"
  ),
  handling = c(
    "Derived liabilities as Assets minus StockholdersEquity",
    "Operating income retained as NA",
    "Used fallback tags and reconstructed missing Q4 from annual less Q1-Q3",
    "Used alternative net income tag as fallback"
  ),
  stringsAsFactors = FALSE
)

reporting_exceptions
goldman_cf <- jsonlite::fromJSON(
  "01_RAW_DATA/sec_historical/starter_20/CIK0000886982.json"
)

goldman_tags <- names(goldman_cf$facts$`us-gaap`)

goldman_tags[
  grepl(
    "Revenue|Revenues|OperatingIncome|NetIncome|ProfitLoss|AssetsCurrent|LiabilitiesCurrent|Cash",
    goldman_tags,
    ignore.case = TRUE
  )
]
reporting_exceptions <- rbind(
  reporting_exceptions,
  data.frame(
    company = "GOLDMAN SACHS GROUP INC",
    issue = "Bank reporting structure differs; no clean comparable operating income/current asset-current liability framework",
    handling = "Use RevenuesNetOfInterestExpense for revenue; retain non-comparable operating/current metrics as NA and treat financial firms separately in analysis",
    stringsAsFactors = FALSE
  )
)
goldman_test_metrics <- list(
  revenue = build_quarterly_flow(
    goldman_cf,
    c(
      "RevenueFromContractWithCustomerExcludingAssessedTax",
      "Revenues",
      "SalesRevenueNet",
      "RevenuesNetOfInterestExpense"
    )
  ),
  operating_income = build_quarterly_flow(
    goldman_cf,
    c("OperatingIncomeLoss")
  ),
  net_income = build_quarterly_flow(
    goldman_cf,
    c("NetIncomeLoss", "ProfitLoss")
  ),
  assets = build_point_in_time_metric(
    goldman_cf,
    c("Assets")
  ),
  current_assets = build_point_in_time_metric(
    goldman_cf,
    c("AssetsCurrent")
  ),
  current_liabilities = build_point_in_time_metric(
    goldman_cf,
    c("LiabilitiesCurrent")
  )
)

sapply(goldman_test_metrics, nrow)
goldman_revenue_test <- build_quarterly_flow(
  goldman_cf,
  c(
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
    "RevenuesNetOfInterestExpense"
  )
)

dim(goldman_revenue_test)
goldman_fundamentals <- build_company_fundamentals(goldman_cf)

dim(goldman_fundamentals)
build_company_fundamentals <- function(company_cf) {
  
  revenue <- build_quarterly_flow(
    company_cf,
    c(
      "RevenueFromContractWithCustomerExcludingAssessedTax",
      "Revenues",
      "SalesRevenueNet",
      "RevenuesNetOfInterestExpense"
    )
  )
  
  operating_income <- build_quarterly_flow(
    company_cf,
    c("OperatingIncomeLoss")
  )
  
  net_income <- build_quarterly_flow(
    company_cf,
    c(
      "NetIncomeLoss",
      "ProfitLoss",
      "NetIncomeLossAvailableToCommonStockholdersBasic"
    )
  )
  
  assets <- build_point_in_time_metric(
    company_cf,
    c("Assets")
  )
  
  current_assets <- build_point_in_time_metric(
    company_cf,
    c("AssetsCurrent")
  )
  
  liabilities <- build_point_in_time_metric(
    company_cf,
    c("Liabilities")
  )
  
  if (nrow(liabilities) == 0) {
    
    equity <- build_point_in_time_metric(
      company_cf,
      c(
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"
      )
    )
    
    if (nrow(assets) > 0 && nrow(equity) > 0) {
      
      liabilities <- merge(
        assets[, c("end", "filed", "val")],
        equity[, c("end", "val")],
        by = "end",
        all.x = TRUE,
        suffixes = c("_assets", "_equity")
      )
      
      liabilities$val <-
        liabilities$val_assets - liabilities$val_equity
      
      liabilities <- liabilities[, c("end", "filed", "val")]
    }
  }
  
  current_liabilities <- build_point_in_time_metric(
    company_cf,
    c("LiabilitiesCurrent")
  )
  
  cash <- build_point_in_time_metric(
    company_cf,
    c(
      "CashAndCashEquivalentsAtCarryingValue",
      "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
      "CashAndDueFromBanks"
    )
  )
  
  # Use revenue as calendar when available,
  # otherwise use assets
  if (nrow(revenue) > 0) {
    
    fundamentals <- revenue[, c("end", "filed", "val")]
    names(fundamentals)[3] <- "revenue"
    
  } else {
    
    fundamentals <- assets[, c("end", "filed")]
    fundamentals$revenue <- NA_real_
  }
  
  add_metric <- function(base, metric, metric_name) {
    
    if (nrow(metric) == 0) {
      base[[metric_name]] <- rep(NA_real_, nrow(base))
      return(base)
    }
    
    temp <- metric[, c("end", "val")]
    names(temp)[2] <- metric_name
    
    merge(base, temp, by = "end", all.x = TRUE)
  }
  
  fundamentals <- add_metric(
    fundamentals, operating_income, "operating_income"
  )
  
  fundamentals <- add_metric(
    fundamentals, net_income, "net_income"
  )
  
  fundamentals <- add_metric(
    fundamentals, assets, "assets"
  )
  
  fundamentals <- add_metric(
    fundamentals, current_assets, "current_assets"
  )
  
  fundamentals <- add_metric(
    fundamentals, liabilities, "liabilities"
  )
  
  fundamentals <- add_metric(
    fundamentals, current_liabilities, "current_liabilities"
  )
  
  fundamentals <- add_metric(
    fundamentals, cash, "cash"
  )
  
  fundamentals <- fundamentals[
    order(fundamentals$end),
  ]
  
  rownames(fundamentals) <- NULL
  
  fundamentals
}
goldman_fundamentals <- build_company_fundamentals(goldman_cf)

dim(goldman_fundamentals)

colSums(is.na(goldman_fundamentals))
for (i in 1:nrow(starter_companies)) {
  
  cat("Testing:", starter_companies$company[i], "\n")
  
  cf <- jsonlite::fromJSON(
    file.path(
      "01_RAW_DATA/sec_historical/starter_20",
      starter_companies$json_file[i]
    )
  )
  
  result <- try(
    build_company_fundamentals(cf),
    silent = TRUE
  )
  
  if (inherits(result, "try-error")) {
    cat("FAILED:", starter_companies$company[i], "\n")
    break
  } else {
    cat("PASSED\n")
  }
}
all_fundamentals_list <- lapply(
  1:nrow(starter_companies),
  function(i) {
    
    cf <- jsonlite::fromJSON(
      file.path(
        "01_RAW_DATA/sec_historical/starter_20",
        starter_companies$json_file[i]
      )
    )
    
    result <- build_company_fundamentals(cf)
    
    result$cik <- starter_companies$cik[i]
    result$company <- starter_companies$company[i]
    
    result
  }
)

all_fundamentals <- do.call(
  rbind,
  all_fundamentals_list
)

dim(all_fundamentals)

colSums(is.na(all_fundamentals))
company_check <- aggregate(
  end ~ company,
  data = all_fundamentals,
  FUN = length
)

names(company_check)[2] <- "quarters"

company_check[order(company_check$quarters), ]
expected_ends <- sort(unique(all_fundamentals$end))

check_missing_quarters <- function(company_name) {
  
  company_dates <- all_fundamentals$end[
    all_fundamentals$company == company_name
  ]
  
  expected_ends[
    !expected_ends %in% company_dates
  ]
}

check_missing_quarters("COCA COLA CO")
check_missing_quarters("WALT DISNEY CO")
check_missing_quarters("EXXON MOBIL CORP")
check_missing_quarters("AMERICAN EXPRESS CO")
subset(
  all_fundamentals,
  company %in% c(
    "COCA COLA CO",
    "WALT DISNEY CO",
    "EXXON MOBIL CORP",
    "AMERICAN EXPRESS CO"
  ),
  select = c(company, end, filed)
)
write.csv(
  all_fundamentals,
  "02_CLEAN_DATA/starter_20_fundamentals.csv",
  row.names = FALSE
)

file.exists(
  "02_CLEAN_DATA/starter_20_fundamentals.csv"
)

#FUNDAMENTALS END HERE - GB

financial_features <- all_fundamentals

financial_features$current_ratio <-
  financial_features$current_assets /
  financial_features$current_liabilities

financial_features$liabilities_to_assets <-
  financial_features$liabilities /
  financial_features$assets

financial_features$return_on_assets <-
  financial_features$net_income /
  financial_features$assets

financial_features$operating_margin <-
  financial_features$operating_income /
  financial_features$revenue

financial_features$cash_to_assets <-
  financial_features$cash /
  financial_features$assets

head(
  financial_features[, c(
    "company",
    "end",
    "current_ratio",
    "liabilities_to_assets",
    "return_on_assets",
    "operating_margin",
    "cash_to_assets"
  )]
)
feature_cols <- c(
  "current_ratio",
  "liabilities_to_assets",
  "return_on_assets",
  "operating_margin",
  "cash_to_assets"
)

# Missing values
colSums(is.na(financial_features[, feature_cols]))

# Infinite values
sapply(
  financial_features[, feature_cols],
  function(x) sum(is.infinite(x))
)

# Summary statistics
summary(financial_features[, feature_cols])

# Make sure data is ordered correctly
financial_features <- financial_features[
  order(financial_features$company, financial_features$end),
]

# Year-over-year revenue growth
financial_features$revenue_growth_yoy <- ave(
  financial_features$revenue,
  financial_features$company,
  FUN = function(x) {
    c(
      rep(NA_real_, 4),
      (x[5:length(x)] / x[1:(length(x) - 4)]) - 1
    )
  }
)

# Year-over-year net income growth
financial_features$net_income_growth_yoy <- ave(
  financial_features$net_income,
  financial_features$company,
  FUN = function(x) {
    c(
      rep(NA_real_, 4),
      (x[5:length(x)] / x[1:(length(x) - 4)]) - 1
    )
  }
)


head(
  financial_features[, c(
    "company",
    "end",
    "revenue",
    "revenue_growth_yoy",
    "net_income",
    "net_income_growth_yoy"
  )],
  10
)


financial_features$operating_margin_change_yoy <- ave(
  financial_features$operating_margin,
  financial_features$company,
  FUN = function(x) {
    c(
      rep(NA_real_, 4),
      x[5:length(x)] - x[1:(length(x) - 4)]
    )
  }
)

financial_features$leverage_change_yoy <- ave(
  financial_features$liabilities_to_assets,
  financial_features$company,
  FUN = function(x) {
    c(
      rep(NA_real_, 4),
      x[5:length(x)] - x[1:(length(x) - 4)]
    )
  }
)

head(
  financial_features[, c(
    "company",
    "end",
    "operating_margin",
    "operating_margin_change_yoy",
    "liabilities_to_assets",
    "leverage_change_yoy"
  )],
  10
)



financial_features$current_ratio_change_yoy <- ave(
  financial_features$current_ratio,
  financial_features$company,
  FUN = function(x) {
    c(
      rep(NA_real_, 4),
      x[5:length(x)] - x[1:(length(x) - 4)]
    )
  }
)

financial_features$cash_to_assets_change_yoy <- ave(
  financial_features$cash_to_assets,
  financial_features$company,
  FUN = function(x) {
    c(
      rep(NA_real_, 4),
      x[5:length(x)] - x[1:(length(x) - 4)]
    )
  }
)
head(
  financial_features[, c(
    "company",
    "end",
    "current_ratio",
    "current_ratio_change_yoy",
    "cash_to_assets",
    "cash_to_assets_change_yoy"
  )],
  10
)


feature_cols_full <- c(
  "current_ratio",
  "liabilities_to_assets",
  "return_on_assets",
  "operating_margin",
  "cash_to_assets",
  "revenue_growth_yoy",
  "net_income_growth_yoy",
  "operating_margin_change_yoy",
  "leverage_change_yoy",
  "current_ratio_change_yoy",
  "cash_to_assets_change_yoy"
)

# Missing values
colSums(
  is.na(financial_features[, feature_cols_full])
)

# Infinite values
sapply(
  financial_features[, feature_cols_full],
  function(x) sum(is.infinite(x))
)

# Summary statistics
summary(
  financial_features[, feature_cols_full]
)
financial_features$return_on_assets_change_yoy <- ave(
  financial_features$return_on_assets,
  financial_features$company,
  FUN = function(x) {
    c(
      rep(NA_real_, 4),
      x[5:length(x)] - x[1:(length(x) - 4)]
    )
  }
)

summary(financial_features$return_on_assets_change_yoy)

sum(is.infinite(
  financial_features$return_on_assets_change_yoy
))


summary(financial_features$return_on_assets_change_yoy)
write.csv(
  financial_features,
  "02_CLEAN_DATA/financial_features_v1.csv",
  row.names = FALSE
)

file.exists(
  "02_CLEAN_DATA/financial_features_v1.csv"
)


financial_features <- merge(
  financial_features,
  ticker_map,
  by = "cik",
  all.x = TRUE
)

head(
  financial_features[, c(
    "company",
    "cik",
    "ticker",
    "end",
    "filed"
  )]
)

sum(is.na(financial_features$ticker))


financial_features$filed <- as.Date(financial_features$filed)
stock_data$date <- as.Date(stock_data$date)

get_first_trading_day <- function(ticker_value, filing_date) {
  
  dates <- stock_data$date[
    stock_data$ticker == ticker_value &
      stock_data$date >= filing_date
  ]
  
  if (length(dates) == 0) {
    return(as.Date(NA))
  }
  
  min(dates)
}

financial_features$market_start_date <- as.Date(
  mapply(
    get_first_trading_day,
    financial_features$ticker,
    financial_features$filed
  ),
  origin = "1970-01-01"
)

head(
  financial_features[, c(
    "company",
    "filed",
    "market_start_date"
  )],
  10
)

sum(is.na(financial_features$market_start_date))

financial_features[
  is.na(financial_features$market_start_date),
  c("company", "ticker", "filed", "end")
]

range(stock_data$date)

table(stock_data$ticker)

calculate_forward_drawdown <- function(ticker_value, start_date) {
  
  if (is.na(start_date)) {
    return(NA_real_)
  }
  
  x <- stock_data[
    stock_data$ticker == ticker_value &
      stock_data$date >= start_date,
  ]
  
  # Need a complete 252-trading-day forward window
  if (nrow(x) < 252) {
    return(NA_real_)
  }
  
  x <- x[order(x$date), ]
  x <- x[1:252, ]
  
  prices <- x$adjusted
  
  running_peak <- cummax(prices)
  
  drawdowns <- prices / running_peak - 1
  
  min(drawdowns, na.rm = TRUE)
}

financial_features$future_drawdown_12m <- mapply(
  calculate_forward_drawdown,
  financial_features$ticker,
  financial_features$market_start_date
)

summary(financial_features$future_drawdown_12m)

sum(is.na(financial_features$future_drawdown_12m))

financial_features$distress_12m <- ifelse(
  is.na(financial_features$future_drawdown_12m),
  NA,
  ifelse(
    financial_features$future_drawdown_12m <= -0.30,
    1,
    0
  )
)

table(
  financial_features$distress_12m,
  useNA = "ifany"
)

distress_by_company <- aggregate(
  distress_12m ~ company,
  data = financial_features,
  FUN = function(x) {
    c(
      observations = length(x),
      distress = sum(x == 1),
      distress_rate = mean(x == 1)
    )
  }
)

distress_by_company

financial_features$year <- as.integer(
  format(financial_features$filed, "%Y")
)

distress_by_year <- aggregate(
  distress_12m ~ year,
  data = financial_features,
  FUN = function(x) {
    c(
      observations = length(x),
      distress = sum(x == 1),
      distress_rate = mean(x == 1)
    )
  }
)

distress_by_year

write.csv(
  financial_features,
  "02_CLEAN_DATA/financial_features_v2.csv",
  row.names = FALSE
)

file.exists(
  "02_CLEAN_DATA/financial_features_v2.csv"
)

model_dataset <- financial_features[
  !is.na(financial_features$distress_12m),
]

dim(model_dataset)

table(model_dataset$distress_12m)

range(model_dataset$filed)

write.csv(
  model_dataset,
  "02_CLEAN_DATA/model_dataset.csv",
  row.names = FALSE
)

file.exists(
  "02_CLEAN_DATA/model_dataset.csv"
)

sum(duplicated(model_dataset[, c("company", "filed")]))

sum(is.na(model_dataset$distress_12m))

file.exists("02_CLEAN_DATA/starter_20_fundamentals.csv")
file.exists("02_CLEAN_DATA/financial_features_v1.csv")
file.exists("02_CLEAN_DATA/financial_features_v2.csv")
file.exists("02_CLEAN_DATA/model_dataset.csv")