import datetime


seatBaseScenario = {'B737' : 135, 'B734' : 159, 'CRJX' : 90, 'B738' : 171, 'B752' : 212, 'B763' : 243, 'B744' : 410, 'A319' : 141, 'A320' : 170, 'A321' : 212, 'AT43' : 44, 'AT76' : 71, 'DH8D' : 72, 'E190' : 96, 'A332' : 295, 'B733' : 134, 'B735' : 114, 'AT72' : 67}


def convDatetime(info): #convert the date of the database to a convenient type to do calculations
	date,clock = info.split(" ")
	year,month,day = date.split("-")
	hours,minutes,seconds = clock.split(':')
	return(datetime.datetime(int(year),int(month),int(day),int(hours),int(minutes),int(seconds)))

	

	
def stayIdentifier(flightList): #give all info about stays in EGLL for one aircraft
	res = []		 #return tuple of flightList : [flightList(arrival),flightList(departure)] 
	for ind,l in enumerate(flightList):
		if l[4] == "EGLL":
			res.append([flightList[ind],flightList[ind+1]]) #if an aircraft lands in EGLL, the next flight will be his departure
	return(res)
	

def generateDic(Larg): #Generate the dictionnary { what we have to pay : price }, adapt the format depending of the number of information in the database
	Largs = [float(k) for k in Larg]
	if len(Largs)==11:
		aux = {'Charge per departing passenger' : Largs[0], 'FEPG' : Largs[1], 'Other destinations, gate' : Largs[2], 'Per departing passenger' : Largs[3], 'PCA' : Largs[4], 'Reduced Rate' : Largs[5], 'Parking 1' : Largs[6], 'Parking 2' : Largs[7], 'Chapter' : Largs[8], 'Charge per approach' : Largs[9], 'Night surcharge' : Largs[10]}
	else:
		aux = {'Charge per departing passenger' : Largs[0], 'FEPG' : Largs[1], 'Other destinations, gate' : Largs[2], 'Per departing passenger' : Largs[3], 'PCA' : Largs[4], 'Reduced Rate' : Largs[5], 'Parking 1' : Largs[6], 'Parking 2' : Largs[7], 'Parking 3' : Largs[8], 'Parking 4' : Largs[9], 'Chapter' : Largs[10], 'Charge per approach' : Largs[11], 'Night surcharge' : Largs[12]}
	return aux




#This function calculate the number of hour that an airplane has to pay for parking, considering that it is free between 23h and 6h and that EGLL offer 30 minutes. "arrival" and "departure" are the dates of arrival and departure of the airplane

def countdownParkingHour(arrival,departure):
	aux = arrival
	due = datetime.timedelta()
	if arrival.hour>22 or arrival.hour<6:
		aux = aux + datetime.timedelta(seconds = (60 - aux.second) % 60)
		aux = aux + datetime.timedelta(minutes = (60 - aux.minute) % 60)
		
	else:
		due = due + datetime.timedelta(seconds = (60 - aux.second) % 60)
		aux = aux + datetime.timedelta(seconds = (60 - aux.second) % 60)
		
		due = due + datetime.timedelta(minutes = (60 - aux.minute) % 60)
		aux = aux + datetime.timedelta(minutes = (60 - aux.minute) % 60)
	
	while (aux + datetime.timedelta(hours = 1)) <= departure:
		if aux.hour>22 or aux.hour<6:
			aux = aux + datetime.timedelta(hours = 1)
		else:
			aux = aux + datetime.timedelta(hours = 1)
			due = due + datetime.timedelta(hours = 1)
	
	while (aux + datetime.timedelta(minutes = 1)) <= departure:
		if aux.hour>22 or aux.hour<6:
			aux = aux + datetime.timedelta(minutes = 1)
		else:
			aux = aux + datetime.timedelta(minutes = 1)
			due = due + datetime.timedelta(minutes = 1)
			
	while (aux + datetime.timedelta(seconds = 1)) <= departure:
		if aux.hour>22 or aux.hour<6:
			aux = aux + datetime.timedelta(seconds = 1)
		else:
			aux = aux + datetime.timedelta(seconds = 1)
			due = due + datetime.timedelta(seconds = 1)	
	due = due - datetime.timedelta(minutes = 90) #the firsts 90 are free
	if due < datetime.timedelta(seconds = 0):
		return(datetime.timedelta(minutes = 0))
	else:
		return(due)
		


def costs(stay, feedic): #compute the price of a stay using the dictionnary of all costs 
	ac_type = stay[0][-1]
	if not ac_type in [k for k in feedic.keys()]:
		return "Error : aircraft not supported"
	else: 
		landingHour = stay[0][-2].hour
		landingDate = stay[0][-2]
		departureDate = stay[1][1]
		passengercosts = feedic[ac_type]['Charge per departing passenger']*seatBaseScenario[ac_type]
		infrastructurecosts = feedic[ac_type]['FEPG'] + feedic[ac_type]['PCA'] 
		parkingcosts = countdownParkingHour(landingDate, departureDate).total_seconds()/60 *  float(feedic[ac_type]['Parking 1']) #not sure where to find the information of the costs or parking per hour..
		landingcosts = feedic[ac_type]['Chapter']
		nightcost = 0 if (landingHour<23 and landingHour >= 6) else feedic[ac_type]['Night surcharge']  
		return(passengercosts + infrastructurecosts + parkingcosts + landingcosts + nightcost) 

def main():

	file = open("EGLL_flights_airac_1810_complete.csv","r")

	SEP = ","  

	dic = {}
	
	#aliases that helps to understand what we takes when we read the file
	num = 0
	ident = 1
	ac_id = 2
	tailno = 3
	ac_type = 4
	aobt = 5
	eobt = 6
	iobt = 7 
	operator = 8 
	arr = 9
	dep = 10
	tr_id_ftfm = 11
	eldt = 12  
	tr_id_ctfm = 13
	aldt = 14
	
	#the list that contains all the types or airplanes that we have recorded
	ac_typeList = []
	
	#Creation of the dictionnary { tailno : list of all the flights recorded }, saved in variable dic
	for line in file:
		ligne = line.split(SEP)
		if (ligne[0] == "num"):
			continue
		else:
			try:
				if (ligne[ac_type] not in ac_typeList):
					ac_typeList.append(ligne[ac_type]) 
				flightList = dic[ligne[tailno]]
				flightList.append([ligne[ident],convDatetime(ligne[aobt]),convDatetime(ligne[eobt]),convDatetime(ligne[iobt]),ligne[arr],ligne[dep],convDatetime(ligne[eldt]),convDatetime(ligne[aldt]), ligne[ac_type]])
			except Exception:
				if (ligne[ac_type] not in ac_typeList):
					ac_typeList.append(ligne[ac_type]) 
				dic[ligne[tailno]] = [[ligne[ident],convDatetime(ligne[aobt]),convDatetime(ligne[eobt]),convDatetime(ligne[iobt]),ligne[arr],ligne[dep],convDatetime(ligne[eldt]),convDatetime(ligne[aldt]), ligne[ac_type]]]
	for clef,value in dic.items(): #we have to sort the flights by the time it landed in order to know how much time they spent in EGLL
		dic[clef].sort(key = lambda x:x[1])
	
		#For instance, the instruction "dic['9VSKN']" give a list of 4 flight, each flight has the following form :
		#['39378', datetime.datetime(2018, 9, 14, 20, 59), datetime.datetime(2018, 9, 14, 21, 5), datetime.datetime(2018, 9, 14, 21, 5), 'WSSS', 'EGLL', datetime.datetime(2018, 9, 15, 9, 24, 57), datetime.datetime(2018, 9, 15, 9, 19, 18), 'A388']
		#[ident, aobt, eobt, iobt, arr, dep, eldt, aldt, ac_type]
	
	#Here we can identify stays in EGLL using the stayIdentifier function :
	stays = stayIdentifier(dic['GEUOH'])
	
	#stay is a list with a length of 2, and stays[0] gives [['90709', datetime.datetime(2018, 9, 13, 8, 40), datetime.datetime(2018, 9, 13, 8, 50), datetime.datetime(2018, 9, 13, 8, 50), 'EGLL', 'EKCH', datetime.datetime(2018, 9, 13, 10, 33, 16), datetime.datetime(2018, 9, 13, 10, 32, 30), 'A319'], ['96216', datetime.datetime(2018, 9, 13, 11, 45), datetime.datetime(2018, 9, 13, 11, 40), datetime.datetime(2018, 9, 13, 11, 40), 'EDDM', 'EGLL', datetime.datetime(2018, 9, 13, 13, 18, 15), datetime.datetime(2018, 9, 13, 13, 23, 11), 'A319']]

	#It means that the airplane 9VSKN landed the 13/09/2018 at 13h08 from EKCH, and took off the 13/09/2018 at 13h23 in the direction of EDDM 
	
	#Creation of the dictionnary { ac_type : dictionnary of prices relative to this airplane } (feeDic), by reading the database and using the function generateDic
	feeDic = {}
	Largs = []
	current_ac = 'A319'
	filefee = open("EGLL_fees.csv","r")
	for line in filefee:
		ligne = line.split(",")
		ac_read = ligne[1]
		ac_read = ac_read[1:len(ac_read)-1]
		if ac_read==current_ac:
			aux = ligne[-1].rstrip('\n')
			aux = aux[1:len(aux)-1]
			Largs.append(aux)
		else:
			feeDic[current_ac] = generateDic(Largs)
			Largs = []
			current_ac = ac_read
	#For instance, feeDic['A319'] returns {'Charge per departing passenger': '2.33', 'FEPG': '0', 'Other destinations, gate': '5338.32', 'Per departing passenger': '66.12', 'PCA': '0', 'Reduced Rate': '9048', 'Parking 1': '143.43', 'Parking 2': '114.75', 'Chapter': '0', 'Charge per approach': '28.69', 'Night surcharge': '2460.09'}, which resume well the database, allowing us to calculate the costs
	
	stay = stays[2]
	print(costs(stay,feeDic))
	
	
	
	

		
		
main()			
	
	
