#!/bin/python
import csv, json

class FluxForeCastGetter():

    def __init__(self):

        self.skip = ['', 'ghi', 'dni', 'dhi', 'mydatetime', 'myTZtimestamp', 'TTT', 'FF', "mytimestamp", 'DCSim']
        self.data = {}
        with open("outputdwdforecast.csv") as stream:

            reader = csv.DictReader(stream, delimiter=",")
            for row in reader:
                k = row['']
                k = k.replace(" ", "T")

                #Fixme: need to figure out if summertime or not
                k = k.replace("+00:00", "")


                #print (row)
                #k = row["timestamp"]
                if k in self.data:
                    print(k, row)
                    raise KeyError

                date, time = k.split("T")

                #Fixme: for now we skip, wouldnt work in australia ;-)
                hour_int  = int ( time[:2] ) -1
                if hour_int <0: continue
                hour = str(hour_int).rjust(2, "0")
                #otherwise ts gets not parsed no idea if need to set flux timezone
                k = date + "T" + hour + time[2:] + "Z"

                self.data[k] = {x: float(y) for x, y in row.items() if x not in self.skip}

                beam = self.data[k]["Rad1h"]
                if beam <= 0.01:
                    if hour_int %2 == 0:
                        self.data[k]["ACSim"] = -0.01
                    else:
                        self.data[k]["ACSim"] =  0.01



        self.jsons = json.dumps(self.data, indent=2)
        print (self.jsons)

## Build Flux Queries, maybe later switch to dedicated flux module...
class FluxMaker():
    def __init__(self, data):
        self.data = data

        self.tpl = """
data =
    array.from(
        rows: [
            //loop
            {
                _time: "@ts@",
                _measurement: "@k@"
                _field: "_value",
                _value: @v@,
            },//loop
            
        ],
    )

data
    |> to(bucket: "forecast")
""".split("//loop")
        self.pfx, self.snippet, self.sfx = self.tpl

        self.bycol = {}
        self.colKeys = set()
        for ts, row in self.data.items():
            self.colKeys |= set( [ k for k in row.keys() ] )

        for col in self.colKeys:
            if col not in self.bycol: self.bycol[col] = {}
            for ts in self.data.keys():
                self.bycol[col][ts] = self.data[ts][col]

        self.jsons = json.dumps( self.bycol, indent=2)
        #print (self.jsons)
        #raise NotImplementedError

        self.qs = {}
        for measurement, details in self.bycol.items():
            self.qs[measurement] = self.pfx
            for ts, val in details.items():
                thisSnip = self.snippet
                for tok, rep in { "ts":ts, "k":measurement, "v":str(val) }.items():
                    thisSnip = thisSnip.replace("@"+tok+"@", rep)
                self.qs[measurement] += thisSnip

            #self.qs[measurement] = self.qs[measurement][:-1]  # snip off last comma
            self.qs[measurement] += self.sfx
            fn = "flux-test/to-"+measurement+".flux"
            with open(fn,"w") as stream:
                stream.write(self.qs[measurement])

if __name__ == "__main__":
    myFluxFcGet = FluxForeCastGetter()
    myFluxes    = FluxMaker( myFluxFcGet.data)