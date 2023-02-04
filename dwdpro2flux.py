#!/bin/python
import csv, json

class FluxForeCastPusher():

    def __init__(self):

        self.skip = ['', 'ghi', 'dni', 'dhi', 'mydatetime', 'myTZtimestamp', 'TTT', 'FF', "mytimestamp", 'DCSim']
        self.data = {}
        with open("outputdwdforecast.csv") as stream:

            reader = csv.DictReader(stream, delimiter=",")
            for row in reader:
                k = row['']
                k = k.replace(" ", "T")

                #Fixme: need to figure out if summertime or not
                k = k.replace("+00:00", "+01:00")


                #print (row)
                #k = row["timestamp"]
                if k in self.data:
                    print(k, row)
                    raise KeyError
                self.data[k] = { x:float(y) for x,y in row.items() if x not in self.skip }
                hour = int ( k.split("T")[-1][:2] )
                beam = self.data[k]["Rad1h"]
                if beam <= 0.01:
                    if hour %2 == 0:
                        self.data[k]["ACSim"] = -0.01
                    else:
                        self.data[k]["ACSim"] =  0.01

        self.jsons = json.dumps(self.data, indent=2)
        print (self.jsons)

if __name__ == "__main__":
    myFluxFCP = FluxForeCastPusher()