import "timezone"

option location = timezone.location(name: "Europe/Berlin")

data = from(bucket: "forecast")
|> range(start: -1d, stop: 2d)
//|> filter(fn: (r) => r._measurement == "ACSim" and r._field == "_value")
|> filter(fn: (r) => r._measurement == "ACSim" )
|> fill(usePrevious: true)
//|> mean()
|> yield()
