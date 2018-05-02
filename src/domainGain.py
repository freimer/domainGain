from fmcprint import *
from expireddomains import *
from namesilo import *
from k9cat import *
from threading import Lock, Thread
import socket

lock = Lock()

fmcp = FmcPrint()

#### ENTER YOUR K9 LICENSE (free @ http://www1.k9webprotection.com/) ####
K9LICENSE = ""

### ENTER YOUR NAMESILO API KEY (free @ https://www.namesilo.com) ####
NSAPIKEY = ""

### ENTER YOUR NAMESILO PAYMENT ID. (free @ https://www.namesilo.com) ###
NSPAYMENTID = ""

#Get variety of recently expired domains from expireddomains.net
fmcp.printDiag("Getting expired domains...")
ed = ExpiredDomains()
edResults = []

def SortByUrlThread():
    global edResults
    global ed
    fmcp.printDiag("Getting Domains Sorted by Url...")
    results = ed.unauthSearch( ed.unauthSearchUrl )

    lock.acquire()
    edResults += results
    lock.release()
    fmcp.printSuccess("Completed Getting Domains Sorted by Url!")

def SortBySimWebThread():
    global edResults
    global ed
    fmcp.printDiag("Getting Domains Sorted by SimWeb Score...")
    results = ed.unauthSearch( ed.unauthSearchSimWebUrl)

    lock.acquire()
    edResults += results
    lock.release()
    fmcp.printSuccess("Completed Getting Domains Sorted by SimWeb Score!")

def SortByAcrScoreThread():
    global edResults
    global ed
    fmcp.printDiag("Getting Domains Sorted by ACR Score...")
    results = ed.unauthSearch( ed.unauthSearchAcrUrl)

    lock.acquire()
    edResults += results
    lock.release()
    fmcp.printSuccess("Completed Getting Domains Sorted by ACR Score!")

threads = []
for func in [SortByUrlThread, SortBySimWebThread, SortByAcrScoreThread]:
    threads.append(Thread(target=func))
    threads[-1].start()

for thread in threads:
    thread.join()

fmcp.printDiag("Sorting results...")
edResults = sorted( set( edResults ) )

fmcp.printSuccess("Found {0} recently expired domains".format( len( edResults ) ) )

#Of the expired domains, find out which are available via NameSilo
fmcp.printDiag("Checking availability of expired domains...")
ns = NameSilo( apiKey = NSAPIKEY, paymentId = NSPAYMENTID )
idx = 0
numUrls = 300
available = []
while (idx + numUrls) < len( edResults ):
    try:
        available += ns.registerAvailability( edResults[idx:idx+numUrls] )
    except:
        fmcp.printWarning("No URLS available from {0} to {1}".format( idx, idx+numUrls ) )

    idx += numUrls

try:
    available += ns.registerAvailability( edResults[idx:] )
except:
    fmcp.printWarning("No URLS available from {0} to {1}".format( idx, len(edResults) ) )

try:
    fmcp.printSuccess("Found {0} of the expired domains are still available".format( len( available ) ) )
except:
    fmcp.printError("None of the recently expired URLS are available")
    sys.exit(0)

#Get categorizations for each of the available domains
fmcp.printDiag("Checking categorization for domains...")
k9 = K9Cat( k9license = K9LICENSE )
domains = {}
blacklist = ["Uncategorized", "Unknown", "Suspicious", "Malicious Outbound Data/Botnets", "Adult/Mature Content", "Pornography", "Malicious Sources/Malnets", "Mixed Content/Potentially Adult", "Scam/Questionable/Illegal", "Phishing"]

for dom in available:
    category = k9.CheckCat( dom )
    if category not in blacklist:
        domains[ dom ] = category

try:
    fmcp.printSuccess("Found {0} domains that have good categorization and are available".format( len( domains ) ) )
except:
    fmcp.printError("None of the recently expired, available domains have good categorizations")
    sys.exit(0)

fmcp.printSuccess("Here is a list of available, categorized domains")
goodDomList = []
idx = 0
for key, val in domains.iteritems():
    fmcp.printSuccessNum("{0}\t\t\t{1}\n".format(key, val), idx)
    idx = idx + 1
    goodDomList.append( key )

choice = -1
ipAddress = ""

while True:
    try:
        choice = input("Please enter the number next to the domain that you would like to register [0-{0}]: ".format(len(goodDomList)))

        if (0 < choice ) and ( choice < len( goodDomList ) ):
            break
        else:
            fmcp.printError("Invalid choice, please choose again")
    except:
        fmcp.printError("Invalid entry, please enter a number")

while True:
    ipAddress = raw_input("Please enter the IP address of the host to which you would like to point the new domain: ")
    try:
        socket.inet_aton(ipAddress)
        break
    except:
        fmcp.printError("Invalid IPv4 Address, please try again")

fmcp.printDiag("Registering {0} and pointing A record to {1}".format( goodDomList[ choice ], ipAddress ) )
ns.RegisterAndSetARecord( goodDomList[ choice ], ipAddress )
fmcp.printSuccess("Successfully setup your categorized domain! Please allow some time for the DNS records to propogate")
