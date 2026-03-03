# Data processing and PVLIB utilities for DWD forecast
import numpy as np
import pandas as pd
import pvlib
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS
import logging

def build_dataframe(mosmixdata, TemperatureOffset):
    mycolumns = {'mydatetime': np.array(mosmixdata[1]),
                 'myTZtimestamp': np.array(mosmixdata[1]),
                 'Rad1h': np.array(mosmixdata[2]),
                 'TTT': np.array(mosmixdata[3]),
                 'PPPP': np.array(mosmixdata[4]),
                 'FF': np.array(mosmixdata[5])}
    df = pd.DataFrame(data=mycolumns)
    df.Rad1h = df.Rad1h.astype(float)
    df.FF = df.FF.astype(float)
    df.PPPP = df.PPPP.astype(float)
    df.TTT = df.TTT.astype(float) + TemperatureOffset
    df['Rad1wh'] = 0.277778 * df.Rad1h
    df.myTZtimestamp = pd.to_datetime(pd.Series(df.myTZtimestamp))
    return df


def run_pvlib(df, pv_system, pv_location, simple_factor):
    first = df.myTZtimestamp.iloc[0]
    last = df.myTZtimestamp.index[-1]
    last = df.myTZtimestamp.iloc[last]
    local_timestamp = pd.date_range(start=first, end=last, freq='1h', tz="UTC")
    df['Rad1Energy'] = simple_factor * df.Rad1wh
    df.index = local_timestamp
    local_unixtimestamp = [time.mktime(ts.timetuple()) for ts in local_timestamp]
    df['mytimestamp'] = np.array(local_unixtimestamp)
    solpos = pvlib.solarposition.get_solarposition(time=local_timestamp,
                                                   latitude=pv_location.latitude,
                                                   longitude=pv_location.longitude,
                                                   altitude=pv_location.altitude)
    DNI = pvlib.irradiance.disc(ghi=df.Rad1wh, solar_zenith=solpos.zenith, datetime_or_doy=local_timestamp, pressure=df.PPPP, min_cos_zenith=0.9, max_zenith=80, max_airmass=12)
    DHI = pvlib.irradiance.erbs(ghi=df.Rad1wh, zenith=solpos.zenith, datetime_or_doy=local_timestamp, min_cos_zenith=0.9, max_zenith=80)
    dataheader = {'ghi': df.Rad1wh, 'dni': DNI.dni, 'dhi': DHI.dhi, 'temp_air': df.TTT, 'wind_speed': df.FF}
    mc_weather = pd.DataFrame(data=dataheader)
    mc_weather.index = local_timestamp
    modelchain = ModelChain(pv_system, pv_location, aoi_model='no_loss', spectral_model='no_loss')
    try:
        modelchain.run_model(mc_weather)
    except Exception as e:
        logging.error("Error running pvlib modelchain: %s", e)
        return df, mc_weather, modelchain
    df['ACSim'] = modelchain.results.ac
    df['CellTempSim'] = modelchain.results.cell_temperature
    df['DCSim'] = modelchain.results.dc.p_mp
    return df, mc_weather, modelchain

