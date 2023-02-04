import "csv"

csv.from(file: "/home/witti/dwdoutputdwdforecast.csv")
|>to(bucket: "forecast")
