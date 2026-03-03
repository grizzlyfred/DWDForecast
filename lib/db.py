# Database operations for DWD forecast
import mysql.connector
import logging

def connect_db(user, password, host, port, database):
    try:
        db = mysql.connector.connect(user=user, passwd=password, host=host, port=port, database=database, autocommit=True)
        cur = db.cursor()
        return db, cur
    except Exception as e:
        logging.error("Unable to connect to database: %s", e)
        return None, None

def addsingle_row(cur, tablename, content):
    cur.execute("describe %s" % tablename)
    allowed_keys = set(row[0] for row in cur.fetchall())
    keys = allowed_keys.intersection(content)
    columns = "`" + "`,`".join(keys) + "`"
    values_template = ", ".join(["%s"] * len(keys))
    sql = "insert into %s (%s) values (%s)" % (tablename, columns, values_template)
    values = tuple(content[key] for key in keys)
    try:
        cur.execute(sql, values)
    except mysql.connector.Error as error:
        logging.error("addsingle_row DB error: %s", error)

def update_row(cur, tablename, TTT, Rad1h, FF, PPPP, mytimestamp, Rad1Energy, ACSim, DCSim, CellTempSim, Rad1wh):
    sql = ("UPDATE " + str(tablename) + " SET " +
           " Rad1h= " + str(Rad1h) + ", PPPP = " + str(PPPP) + ", FF= " + str(FF) + ", TTT= " + str(TTT) +
           ", Rad1Energy= " + str(Rad1Energy) + ", ACSim= " + str(ACSim) + ", DCSim = " + str(DCSim) +
           ", CellTempSim =" + str(CellTempSim) + ", Rad1wh =" + str(Rad1wh) + " WHERE mytimestamp= " + str(mytimestamp))
    try:
        cur.execute(sql)
    except mysql.connector.Error as error:
        logging.error("update_row DB error: %s", error)

def find_last_timestamp(cur, mytable):
    mytimestamp = 'mytimestamp'
    myquery = "select %s from %s order by mytimestamp desc limit 1" % (mytimestamp, mytable)
    cur.execute(myquery)
    myresult = cur.fetchall()
    rowcount = cur.rowcount
    if rowcount < 1:
        return 0
    myresult = str(myresult[0])
    myresult = myresult.split('(')[1].split(',')[0]
    return int(myresult)

def check_timestamp_existence(cur, mytable, timetocheck):
    mytimestamp = 'mytimestamp'
    myquery = "select %s from %s where %s = %s" % (mytimestamp, mytable, mytimestamp, timetocheck)
    cur.execute(myquery)
    rowcount = cur.rowcount
    return 0 if rowcount < 1 else 1

