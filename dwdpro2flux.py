#!/usr/bin/env python3
import csv, json, os, subprocess

class FluxForeCastGetter():

    def __init__(self):

        self.skip = ['', 'ghi', 'dni', 'dhi', 'mydatetime', 'myTZtimestamp', 'TTT', 'FF', "mytimestamp", 'DCSim']
        self.data = {}

        self.rt = "/home/witti/dwd.git"
        self.fn = "outputdwdforecast.csv"

        self.sourceUri = os.path.join(self.rt, self.fn)
        with open(self.sourceUri) as stream:

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



        #self.jsons = json.dumps(self.data, indent=2)
        #print (self.jsons)

## Build Flux Queries, maybe later switch to dedicated flux module...
class FluxMaker():
    def __init__(self, data):
        self.data = data

        self.tpl = \
"""import "array"
data =
    array.from(
        rows: [//loop
            {
                _time: @ts@,
                _measurement: "@k@",
                _field: "value",
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
            rt = "/home/witti/dwd.git"
            rp = "flux-test"
            fn = "to-"+measurement+".flux"
            self.qUri = os.path.abspath( os.path.join(rt, rp, fn) )
            #print (self.qUri)
            #raise NotImplementedError
            with open(self.qUri,"w") as stream:
                stream.write(self.qs[measurement])

class FluxPusher():
    def __init__(self):
        rt = "/home/witti/dwd.git"
        rp = "flux-test"
        self.pushUri = os.path.abspath( os.path.join(rt, rp) )
        #print ("stf", os.listdir(self.pushUri))
        files = [ x for x in os.listdir(self.pushUri) if os.path.isfile( os.path.join(self.pushUri, x)) and x.endswith(".flux") ]

        print ("found:", files)
        for fluxfile in files:
            self.fluxUri = os.path.abspath( os.path.join(self.pushUri, fluxfile) )
            cmd = ["influx query -o site --file " + self.fluxUri ]
            print ("="*50, os.linesep, cmd)
            res = subprocess.run(cmd, shell=True, capture_output=True, check=True)
            print ("="*50, fluxfile, "Exit:", res.returncode)
            print (res.stdout.decode("utf-8"))
            if res.returncode != 0:
                print ("-"*50, "stderr")
                print (res.stderr.decode("utf-8"))

if __name__ == "__main__":
    myFluxFcGet = FluxForeCastGetter()
    myFluxes    = FluxMaker( myFluxFcGet.data)
    myPusher    = FluxPusher()
