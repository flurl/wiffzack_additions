import pymssql
import sys
import tomllib
from pathlib import Path
from typing import Any
from decimal import Decimal

SCRIPT_DIR: Path = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH: Path = SCRIPT_DIR / "../server/config.toml"
USER_CONFIG_DIR: Path = Path.home() / ".wiffzack_additions"
USER_CONFIG_PATH: Path = USER_CONFIG_DIR / "config.toml"

config: dict[str, Any] = {}
try:
    with open(DEFAULT_CONFIG_PATH, "rb") as f:
        config = tomllib.load(f)
except FileNotFoundError:
    print(
        f"Default configuration file not found at {DEFAULT_CONFIG_PATH}. Exiting.")
    exit(1)  # Good to exit if default is missing too
except tomllib.TOMLDecodeError as e:
    print(
        f"Error decoding default configuration file {DEFAULT_CONFIG_PATH}: {e}. Exiting.")
    exit(1)

try:
    with open(USER_CONFIG_PATH, "rb") as f:
        config_user: dict[str, Any] = tomllib.load(f)
        # This is fine if client.toml replaces whole sections like [client]
        config |= config_user
except FileNotFoundError:
    print(
        f"Client config not found. Please create a '{USER_CONFIG_PATH}' file.")
    exit(1)
except tomllib.TOMLDecodeError as e:
    print(
        f"Error decoding user configuration file {USER_CONFIG_PATH}: {e}. Exiting.")
    exit(1)

# Set database connection parameters
HOST = config["database"]["server"]
USER = config["database"]["username"]
PASSWORD = config["database"]["password"]
DATABASE = config["database"]["database"]

con = pymssql.connect(host=HOST, user=USER, password=PASSWORD, database=DATABASE, tds_version=r"7.0")
cur = con.cursor()
query = """
    select checkpoint_info, checkpoint_id from journal_checkpoints
    where checkpoint_typ = 1
    order by CONVERT(DATE, CAST(checkpoint_info AS NVARCHAR(MAX)), 104) desc
"""
cur.execute(query)
checkpoints = []
i = 1
for res in cur.fetchall():
    checkpoints.append((i, res[0], res[1]))
    i += 1
    
for cp in reversed(checkpoints):
    print("[%s] %s" % (cp[0], cp[1]))
    
query = "select rechnung_id from rechnungen_basis where checkpoint_tag is null"
cur.execute(query)
res = cur.fetchall()	
if len(res) > 0:
    print("[0] ohne TA")
print("press enter for exit")
while True:
    choice = input("? ")
    if choice == "":
        sys.exit()
    try:
        choice = int(choice) - 1
    except ValueError:
        continue
    
    if choice == -1:
        query = "select rechnung_kellnerKurzName, dbo.getWarengruppe(rechnung_detail_artikel_gruppe), sum(rechnung_detail_preis*rechnung_detail_menge) \
        from rechnungen_details, rechnungen_basis \
        where 1=1 \
        and rechnung_detail_rechnung = rechnung_id \
        and checkpoint_tag is null \
        group by rechnung_kellnerKurzName, dbo.getWarengruppe(rechnung_detail_artikel_gruppe) \
        order by 1, 2"
    
    else:
        query = "select rechnung_kellnerKurzName, dbo.getWarengruppe(rechnung_detail_artikel_gruppe), sum(rechnung_detail_preis*rechnung_detail_menge) \
        from rechnungen_details, rechnungen_basis \
        where 1=1 \
        and rechnung_detail_rechnung = rechnung_id \
        and checkpoint_tag = %s \
        group by rechnung_kellnerKurzName, dbo.getWarengruppe(rechnung_detail_artikel_gruppe) \
        order by 1, 2" % checkpoints[choice][2]
    #print(query)
    if choice == -1:
        print("ohne TA")
    else:
        print(checkpoints[choice][1])
        
    cur.execute(query)
    sum = Decimal('0.0')
    for res in cur.fetchall():
        print("%s, %s, %s" % (res[0], res[1], res[2]))
        sum += res[2]
    print("-"*80 + "")
    print("Summe: %s" % sum)
    print("=" * 80 + "\n")