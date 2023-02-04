import "timezone"
import "date"

option location = timezone.location(name: "Europe/Berlin")

startpoint = date.add(d: 1d,  to: today()  )
midnight =   date.add(d: 24h, to: startpoint )

data = from(bucket: "forecast")
|> range(start: startpoint, stop: midnight)
|> filter(fn: (r) => r._measurement == "ACSim" and r._field == "value")
|> fill(usePrevious: true)
|> sum()
|> yield()
