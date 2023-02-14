import "timezone"
import "date"
import "math"

option location = timezone.location(name: "Europe/Berlin")

startpoint = date.add(d: 0d, to: now()    )
midnight   = date.add(d: 1d, to: startpoint )

data = from(bucket: "forecast")
|> range(start: startpoint, stop: midnight)
|> filter(fn: (r) => r._measurement == "temp_air" and r._field == "value")
|> fill(usePrevious: true)
|> max()

data
|> duplicate(column: "_start", as: "_time")
|> drop(columns: ["_start", "_stop" ] )
|> map(fn: (r) => ({r with _value: math.ceil(x: r._value)}))
|> yield()
